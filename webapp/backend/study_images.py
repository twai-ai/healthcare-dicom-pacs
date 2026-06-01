"""
Find DICOM files for patients and attach PNG previews to ImageStatistics.
"""

from pathlib import Path
from typing import Optional

import numpy as np
import pydicom
from sqlalchemy.orm import Session

import models
from image_processor import ImageProcessor

DATA_ROOT = Path("/data/raw")


def resolve_dicom_path(file_path: Optional[str]) -> Optional[Path]:
    """Map host or container paths to an existing DICOM file."""
    if not file_path or str(file_path).strip() in ("", "Unknown", "nan"):
        return None

    path_str = str(file_path).strip()
    candidates = [Path(path_str)]

    if "/data/raw/" in path_str:
        candidates.insert(0, DATA_ROOT / path_str.split("/data/raw/", 1)[1])

    markers = ("/DICOM-AI/data/raw/", "data/raw/")
    for marker in markers:
        if marker in path_str:
            candidates.insert(0, DATA_ROOT / path_str.split(marker, 1)[1])

    for candidate in candidates:
        if candidate.exists() and candidate.suffix.lower() == ".dcm":
            return candidate

    return None


def find_dicom_for_patient(
    patient_id: str, hint_path: Optional[str] = None
) -> Optional[Path]:
    """Locate a representative DICOM for a patient."""
    resolved = resolve_dicom_path(hint_path)
    if resolved:
        return resolved

    patient_dir = DATA_ROOT / "COVID-19-AR" / patient_id
    if patient_dir.is_dir():
        for dcm in sorted(patient_dir.rglob("*.dcm")):
            return dcm

    if DATA_ROOT.is_dir():
        for dcm in DATA_ROOT.rglob("*.dcm"):
            if patient_id in dcm.parts:
                return dcm

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
        for _, row in df.iterrows():
            pid = row.get("patient_id")
            fp = row.get("file_path")
            if pid and fp and pid not in path_hints:
                path_hints[str(pid)] = str(fp)

    studies = db.query(models.Study).all()
    synced = 0

    print("\n" + "=" * 70)
    print("SYNCING SCAN IMAGES")
    print("=" * 70)

    for study in studies:
        dicom_path = find_dicom_for_patient(
            study.patient_id, path_hints.get(study.patient_id)
        )
        if not dicom_path:
            print(f"  ⚠ No DICOM found for {study.patient_id}")
            continue

        if upsert_study_images(db, study, dicom_path):
            synced += 1
            print(f"  ✓ {study.patient_id} ← {dicom_path.name}")

    db.commit()
    with_images = (
        db.query(models.ImageStatistics)
        .filter(models.ImageStatistics.main_image_data.isnot(None))
        .count()
    )
    print(f"\n✅ Synced {synced} studies ({with_images} with images in DB)\n")
    return synced
