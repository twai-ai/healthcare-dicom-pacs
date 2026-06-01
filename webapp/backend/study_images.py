"""
Find DICOM files for patients and attach PNG previews to ImageStatistics.
Uses object storage (S3/R2) or local filesystem via object_storage module.
"""

from pathlib import Path
from typing import Optional

import numpy as np
import pydicom
from sqlalchemy.orm import Session

import models
from image_processor import ImageProcessor
from object_storage import (
    DICOM_PREFIX,
    LOCAL_ROOT,
    find_local_dicom_path,
    get_storage,
    normalize_dicom_key,
    open_data_file,
)


def find_dicom_key_for_patient(
    db: Session,
    patient_id: str,
    hint_path: Optional[str] = None,
) -> Optional[str]:
    """Resolve canonical object key for a patient's DICOM."""
    storage = get_storage()

    if hint_path:
        key = normalize_dicom_key(hint_path)
        if key and storage.exists(key):
            return key
        imported = storage.import_legacy_dicom(
            hint_path, patient_id, study_uid=patient_id
        )
        if imported and storage.exists(imported):
            return imported

    meta = (
        db.query(models.DICOMMetadata)
        .join(models.Study)
        .filter(models.Study.patient_id == patient_id)
        .filter(models.DICOMMetadata.image_path.isnot(None))
        .first()
    )
    if meta and meta.image_path:
        key = normalize_dicom_key(meta.image_path)
        if key and storage.exists(key):
            return key

    prefix = f"{DICOM_PREFIX}{patient_id}/"
    keys = storage.list_keys(prefix)
    if keys:
        return sorted(keys)[0]

    if not storage.use_s3:
        local = find_local_dicom_path(patient_id, hint_path)
        if local:
            key = normalize_dicom_key(str(local))
            if key and storage.exists(key):
                return key
            try:
                rel = local.resolve().relative_to(LOCAL_ROOT.resolve())
                return f"{DICOM_PREFIX}{rel.as_posix()}"
            except ValueError:
                return normalize_dicom_key(str(local))

    return None


def upsert_study_images(db: Session, study: models.Study, dicom_path: Path) -> bool:
    """Generate and store scan previews for a study."""
    try:
        images = ImageProcessor.generate_analysis_images(str(dicom_path))
        if not images.get("has_images"):
            return False

        ds = pydicom.dcmread(str(dicom_path))
        pixel = ds.pixel_array.astype(float)

        stats = (
            db.query(models.ImageStatistics)
            .filter(models.ImageStatistics.study_id == study.id)
            .first()
        )

        if not stats:
            stats = models.ImageStatistics(study_id=study.id)
            db.add(stats)

        stats.main_image_data = images.get("main_image")
        stats.histogram_image_data = images.get("histogram")
        stats.windowed_image_data = images.get("windowed_image")
        stats.mean_intensity = float(np.mean(pixel))
        stats.std_intensity = float(np.std(pixel))
        stats.min_intensity = float(np.min(pixel))
        stats.max_intensity = float(np.max(pixel))
        stats.median_intensity = float(np.median(pixel))
        stats.snr = float(np.mean(pixel) / max(np.std(pixel), 1.0))
        stats.contrast = float(
            (np.max(pixel) - np.min(pixel)) / max(np.mean(pixel), 1.0)
        )

        db.flush()
        return True
    except Exception as exc:
        print(f"  ✗ Image sync failed for {study.patient_id}: {exc}")
        return False


def sync_all_study_images(db: Session, metadata_csv: Optional[Path] = None) -> int:
    """Attach scan images for every study in the database."""
    import pandas as pd

    path_hints = {}
    if metadata_csv and metadata_csv.exists():
        df = pd.read_csv(metadata_csv)
    else:
        try:
            with open_data_file("dicom_metadata.csv") as csv_path:
                df = pd.read_csv(csv_path)
        except FileNotFoundError:
            df = None

    if df is not None:
        for _, row in df.iterrows():
            pid = row.get("patient_id") or row.get("PatientID")
            fp = row.get("file_path")
            if pid and fp and pid not in path_hints:
                path_hints[str(pid)] = str(fp)

    studies = db.query(models.Study).all()
    synced = 0
    storage = get_storage()

    print("\n" + "=" * 70)
    print("SYNCING SCAN IMAGES")
    print("=" * 70)

    for study in studies:
        dicom_key = find_dicom_key_for_patient(
            db, study.patient_id, path_hints.get(study.patient_id)
        )
        if not dicom_key:
            print(f"  ⚠ No DICOM found for {study.patient_id}")
            continue

        try:
            with storage.open_local_copy(dicom_key) as dicom_path:
                if upsert_study_images(db, study, dicom_path):
                    synced += 1
                    print(f"  ✓ {study.patient_id} ← {dicom_key}")
        except FileNotFoundError:
            print(f"  ⚠ Missing object for {study.patient_id}: {dicom_key}")

    db.commit()
    with_images = (
        db.query(models.ImageStatistics)
        .filter(models.ImageStatistics.main_image_data.isnot(None))
        .count()
    )
    print(f"\n✅ Synced {synced} studies ({with_images} with images in DB)\n")
    return synced

