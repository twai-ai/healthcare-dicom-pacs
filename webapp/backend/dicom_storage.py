"""
DICOM persistence: object storage keys + PostgreSQL metadata.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pydicom
from sqlalchemy.orm import Session

import models
from object_storage import build_dicom_key, get_storage, storage_enabled
def storage_status() -> dict:
    from object_storage import DICOM_PREFIX, LOCAL_ROOT

    storage = get_storage()
    return {
        "backend": "s3" if storage.use_s3 else "local",
        "bucket": storage.bucket if storage.use_s3 else None,
        "local_root": str(LOCAL_ROOT),
        "dicom_prefix": DICOM_PREFIX,
    }


def store_uploaded_dicom(
    tmp_path: Path,
    patient_id: str,
    study_instance_uid: str,
    filename: str,
) -> str:
    """Persist uploaded DICOM to storage; return object key."""
    storage = get_storage()
    key = build_dicom_key(patient_id, study_instance_uid, filename)
    return storage.put_file(key, tmp_path)


def upsert_dicom_metadata(
    db: Session,
    study: models.Study,
    storage_key: str,
    dicom_path: Path,
) -> models.DICOMMetadata:
    ds = pydicom.dcmread(str(dicom_path), stop_before_pixels=True)
    sop_uid = str(ds.get("SOPInstanceUID", f"sop-{study.id}"))
    series_uid = str(ds.get("SeriesInstanceUID", f"series-{study.id}"))

    existing = (
        db.query(models.DICOMMetadata)
        .filter(models.DICOMMetadata.study_id == study.id)
        .first()
    )
    if existing:
        existing.image_path = storage_key
        existing.sop_instance_uid = sop_uid
        existing.series_instance_uid = series_uid
        existing.rows = int(ds.get("Rows", 0) or 0)
        existing.columns = int(ds.get("Columns", 0) or 0)
        db.flush()
        return existing

    record = models.DICOMMetadata(
        study_id=study.id,
        series_instance_uid=series_uid,
        sop_instance_uid=sop_uid,
        image_path=storage_key,
        rows=int(ds.get("Rows", 0) or 0),
        columns=int(ds.get("Columns", 0) or 0),
        protocol_name=str(ds.get("StudyDescription", "")),
    )
    db.add(record)
    db.flush()
    return record


def persist_analysis_from_upload(
    db: Session,
    tmp_path: Path,
    result: dict,
    original_filename: str,
) -> dict:
    """
    Save completed analysis to PostgreSQL and object storage.
    Returns dict with patient_id, study_id, dicom_key.
    """
    if result.get("status") != "complete":
        return result

    metadata = result.get("metadata", {})
    patient_id = metadata.get("patient_id")
    study_uid = metadata.get("study_instance_uid")

    patient = (
        db.query(models.Patient)
        .filter(models.Patient.patient_id == patient_id)
        .first()
    )
    if not patient:
        patient = models.Patient(
            patient_id=patient_id,
            patient_name=metadata.get("patient_name"),
            patient_age=metadata.get("patient_age"),
            patient_sex=metadata.get("patient_sex"),
        )
        db.add(patient)
        db.flush()

    study = (
        db.query(models.Study)
        .filter(models.Study.study_instance_uid == study_uid)
        .first()
    )
    if not study:
        study = models.Study(
            patient_id=patient_id,
            study_instance_uid=study_uid,
            study_description=metadata.get("study_description"),
            modality=metadata.get("modality"),
            body_part=metadata.get("body_part"),
            manufacturer=metadata.get("manufacturer"),
            manufacturer_model=metadata.get("manufacturer_model"),
        )
        db.add(study)
        db.flush()
    else:
        db.query(models.DiagnosticAnalysis).filter(
            models.DiagnosticAnalysis.study_id == study.id
        ).delete()
        db.query(models.AIAnalysis).filter(
            models.AIAnalysis.study_id == study.id
        ).delete()
        db.commit()

    storage_key = store_uploaded_dicom(
        tmp_path, patient_id, study_uid, original_filename
    )
    upsert_dicom_metadata(db, study, storage_key, tmp_path)

    diagnostic = result.get("diagnostic", {})
    db.add(
        models.DiagnosticAnalysis(
            patient_id=patient_id,
            study_id=study.id,
            covid_score=diagnostic.get("covid_score"),
            covid_probability=diagnostic.get("covid_probability"),
            severity=diagnostic.get("severity"),
            confidence=diagnostic.get("confidence"),
            clinical_reasoning=diagnostic.get("clinical_reasoning"),
            recommendations=diagnostic.get("recommendations"),
            quantitative_features=diagnostic.get("quantitative_features", {}),
        )
    )

    from study_images import upsert_study_images

    upsert_study_images(db, study, tmp_path)

    ai_results = result.get("ai_analysis", {}).get("models", {})
    for model_name, ai_data in ai_results.items():
        if "analysis" in ai_data:
            db.add(
                models.AIAnalysis(
                    patient_id=patient_id,
                    study_id=study.id,
                    model_name=ai_data.get("model", model_name),
                    analysis_type="vision",
                    findings=ai_data.get("analysis"),
                    analysis_json=ai_data,
                )
            )

    db.commit()

    result["database_saved"] = True
    result["patient_id"] = patient_id
    result["study_id"] = study.id
    result["dicom_storage_key"] = storage_key
    result["storage_backend"] = "s3" if storage_enabled() else "local"
    return result
