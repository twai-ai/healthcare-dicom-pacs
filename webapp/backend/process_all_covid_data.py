"""
Ingest TCIA COVID-19-AR studies from /data/raw/COVID-19-AR into PostgreSQL.

One representative DICOM per patient (prefers CR/DX; for CT uses middle slice).
Replaces placeholder studies for patients being imported.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pydicom

sys.path.insert(0, "/app")
from repo_path import ensure_repo_on_sys_path

ensure_repo_on_sys_path()

from database import SessionLocal
import models
from image_processor import ImageProcessor
from object_storage import normalize_dicom_key
from core.diagnostic_engine import DiagnosticEngine

DICOM_DIR = Path("/data/raw/COVID-19-AR")
_MODALITY_PRIORITY = {"CR": 0, "DX": 1, "CT": 2}
_engine = DiagnosticEngine()


def _fit_varchar(value, max_len: int = 50) -> Optional[str]:
    if value is None:
        return None
    return str(value)[:max_len]


def _parse_age(age_str) -> Optional[int]:
    if not age_str:
        return None
    try:
        return int(str(age_str).replace("Y", "").strip())
    except (TypeError, ValueError):
        return None


def _parse_study_date(value: str) -> Optional[date]:
    if not value or len(str(value)) < 8:
        return None
    try:
        return datetime.strptime(str(value)[:8], "%Y%m%d").date()
    except ValueError:
        return None


def discover_representative_dicoms(dicom_dir: Path) -> Dict[str, Path]:
    """Map patient_id -> one DICOM path per patient."""
    by_patient_modality: Dict[str, Dict[str, List[Path]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for dcm_path in dicom_dir.rglob("*.dcm"):
        try:
            ds = pydicom.dcmread(str(dcm_path), stop_before_pixels=True)
            patient_id = str(getattr(ds, "PatientID", "") or "").strip()
            modality = str(getattr(ds, "Modality", "Unknown") or "Unknown")
            if not patient_id:
                continue
            by_patient_modality[patient_id][modality].append(dcm_path)
        except Exception:
            continue

    chosen: Dict[str, Path] = {}
    for patient_id, modality_map in sorted(by_patient_modality.items()):
        modality = min(
            modality_map.keys(),
            key=lambda m: _MODALITY_PRIORITY.get(m, 99),
        )
        files = sorted(modality_map[modality])
        chosen[patient_id] = files[len(files) // 2]
    return chosen


def delete_patient_studies(db, patient_id: str) -> None:
    """Remove existing studies and related rows for a patient (e.g. showcase placeholders)."""
    studies = (
        db.query(models.Study).filter(models.Study.patient_id == patient_id).all()
    )
    study_ids = [s.id for s in studies]
    if not study_ids:
        return

    for model, col in (
        (models.ImageStatistics, "study_id"),
        (models.DICOMMetadata, "study_id"),
        (models.ProtocolAnalysis, "study_id"),
        (models.QualityMetrics, "study_id"),
        (models.DiagnosticAnalysis, "study_id"),
        (models.AIAnalysis, "study_id"),
    ):
        db.query(model).filter(getattr(model, col).in_(study_ids)).delete(
            synchronize_session=False
        )

    db.query(models.Study).filter(models.Study.patient_id == patient_id).delete(
        synchronize_session=False
    )


def ingest_dicom(db, dcm_path: Path) -> bool:
    try:
        ds = pydicom.dcmread(str(dcm_path))
        patient_id = str(ds.get("PatientID", dcm_path.parent.name))
        study_uid = str(ds.get("StudyInstanceUID", f"study-{dcm_path.stem}"))
        series_uid = str(ds.get("SeriesInstanceUID", f"series-{dcm_path.stem}"))
        sop_uid = str(ds.get("SOPInstanceUID", f"sop-{dcm_path.stem}"))

        delete_patient_studies(db, patient_id)

        patient = (
            db.query(models.Patient)
            .filter(models.Patient.patient_id == patient_id)
            .first()
        )
        age = _parse_age(ds.get("PatientAge", ""))
        if not patient:
            patient = models.Patient(
                patient_id=patient_id,
                patient_name=str(ds.get("PatientName", patient_id)),
                patient_age=age,
                patient_sex=str(ds.get("PatientSex", "U")),
            )
            db.add(patient)
            db.flush()
            print(f"  ✓ Patient: {patient_id} ({age}Y {patient.patient_sex})")
        else:
            if age is not None:
                patient.patient_age = age
            print(f"  ✓ Patient: {patient_id} (updated)")

        study = models.Study(
            patient_id=patient_id,
            study_instance_uid=study_uid,
            study_date=_parse_study_date(str(ds.get("StudyDate", ""))),
            study_description=str(ds.get("StudyDescription", "Chest imaging")),
            modality=str(ds.get("Modality", "Unknown")),
            body_part=str(ds.get("BodyPartExamined", "CHEST")),
            institution_name=str(ds.get("InstitutionName", "Unknown")),
            manufacturer=str(ds.get("Manufacturer", "Unknown")),
            manufacturer_model=str(ds.get("ManufacturerModelName", "Unknown")),
        )
        db.add(study)
        db.flush()

        image_key = normalize_dicom_key(str(dcm_path)) or str(dcm_path)

        db.add(
            models.DICOMMetadata(
                study_id=study.id,
                series_instance_uid=series_uid,
                sop_instance_uid=sop_uid,
                image_path=image_key,
                rows=int(ds.get("Rows", 0) or 0),
                columns=int(ds.get("Columns", 0) or 0),
                pixel_spacing=str(ds.get("PixelSpacing", "")),
                slice_thickness=float(ds.get("SliceThickness", 0))
                if ds.get("SliceThickness")
                else None,
                kvp=float(ds.get("KVP", 0)) if ds.get("KVP") else None,
                exposure_time=float(ds.get("ExposureTime", 0))
                if ds.get("ExposureTime")
                else None,
                protocol_name=str(ds.get("StudyDescription", "")),
            )
        )

        db.add(
            models.ProtocolAnalysis(
                study_id=study.id,
                protocol_name=str(ds.get("StudyDescription", "Unknown")),
                manufacturer=str(ds.get("Manufacturer", "Unknown")),
                model_name=str(ds.get("ManufacturerModelName", "Unknown")),
                slice_thickness=float(ds.get("SliceThickness", 0))
                if ds.get("SliceThickness")
                else None,
                kvp=float(ds.get("KVP", 0)) if ds.get("KVP") else None,
                standardization_score=0.85,
                drift_detected=False,
            )
        )

        db.add(
            models.QualityMetrics(
                study_id=study.id,
                has_required_tags=True,
                has_pixel_data=hasattr(ds, "pixel_array"),
                standardized_orientation=True,
                consistent_spacing=True,
                compliance_score=0.95,
                issues_found=[],
            )
        )

        if hasattr(ds, "pixel_array"):
            pixels = ds.pixel_array.astype(float)
            stats = {
                "mean": float(np.mean(pixels)),
                "std": float(np.std(pixels)),
                "min": float(np.min(pixels)),
                "max": float(np.max(pixels)),
                "median": float(np.median(pixels)),
            }
            stats["snr"] = stats["mean"] / max(stats["std"], 1)
            stats["contrast"] = (stats["max"] - stats["min"]) / max(
                stats["mean"], 1
            )

            print("  📊 Generating previews...")
            images = ImageProcessor.generate_analysis_images(str(dcm_path))
            db.add(
                models.ImageStatistics(
                    study_id=study.id,
                    mean_intensity=stats["mean"],
                    std_intensity=stats["std"],
                    min_intensity=stats["min"],
                    max_intensity=stats["max"],
                    median_intensity=stats["median"],
                    snr=stats.get("snr", 0),
                    contrast=stats.get("contrast", 0),
                    main_image_data=images.get("main_image")
                    if images.get("has_images")
                    else None,
                    histogram_image_data=images.get("histogram")
                    if images.get("has_images")
                    else None,
                    windowed_image_data=images.get("windowed_image")
                    if images.get("has_images")
                    else None,
                )
            )

            findings = _engine.analyze(ds)
            legacy = findings.legacy_diagnostic_dict()
            db.add(
                models.DiagnosticAnalysis(
                    patient_id=patient_id,
                    study_id=study.id,
                    covid_score=legacy.get("covid_score"),
                    covid_probability=_fit_varchar(legacy.get("covid_probability")),
                    severity=_fit_varchar(legacy.get("severity")),
                    confidence=_fit_varchar(legacy.get("confidence")),
                    clinical_reasoning=legacy.get("clinical_reasoning"),
                    differential_diagnosis="; ".join(
                        findings.differential_considerations
                    ),
                    recommendations=legacy.get("recommendations"),
                    quantitative_features=legacy.get("quantitative_features", stats),
                    findings_json=legacy.get("findings_json"),
                    engine_version=findings.engine_version,
                )
            )
            obs = findings.observations
            print(
                f"  ✓ {study.modality} study | pattern {obs.pattern_score}/5 ({obs.pattern_label})"
            )
        else:
            print(f"  ✓ {study.modality} study (no pixel data)")

        return True
    except Exception as exc:
        db.rollback()
        print(f"  ✗ Failed {dcm_path.name}: {exc}")
        return False


def update_bias_analysis(db) -> None:
    patient_count = db.query(models.Patient).count()
    study_count = db.query(models.Study).count()
    manufacturers = db.query(models.Study.manufacturer).distinct().count()
    modalities = db.query(models.Study.modality).distinct().count()

    db.query(models.BiasAnalysis).delete()

    if patient_count < 10:
        risk, score = "HIGH", 0.65
    elif patient_count < 50:
        risk, score = "MEDIUM", 0.45
    else:
        risk, score = "LOW", 0.25

    db.add(
        models.BiasAnalysis(
            analysis_date=date.today(),
            total_patients=patient_count,
            total_studies=study_count,
            manufacturer_diversity=min(manufacturers / 5.0, 1.0),
            protocol_diversity=min(modalities / 3.0, 1.0),
            bias_risk_level=risk,
            bias_score=score,
            recommendations=(
                f"TCIA COVID-19-AR ingest: {patient_count} patients, {study_count} studies. "
                + (
                    "Dataset suitable for validation (50–100 target met)."
                    if patient_count >= 50
                    else "Expand toward 50–100 cases for validation."
                )
            ),
            metrics_json={
                "source": "TCIA COVID-19-AR",
                "total_patients": patient_count,
                "total_studies": study_count,
                "manufacturers": manufacturers,
                "modalities": modalities,
            },
        )
    )


def main() -> None:
    db = SessionLocal()
    print("\n" + "=" * 70)
    print("INGEST TCIA COVID-19-AR → PostgreSQL")
    print("=" * 70)

    if not DICOM_DIR.is_dir():
        print(f"✗ Missing directory: {DICOM_DIR}")
        db.close()
        return

    representatives = discover_representative_dicoms(DICOM_DIR)
    print(f"\n📁 {len(representatives)} patients under {DICOM_DIR}\n")

    if not representatives:
        print("✗ No DICOM files found")
        db.close()
        return

    ok = 0
    for idx, (patient_id, dcm_path) in enumerate(sorted(representatives.items()), 1):
        print(f"\n[{idx}/{len(representatives)}] {patient_id} ← {dcm_path.name}")
        try:
            if ingest_dicom(db, dcm_path):
                db.commit()
                ok += 1
        except Exception as exc:
            db.rollback()
            print(f"  ✗ Rolled back: {exc}")

    db.commit()
    update_bias_analysis(db)
    db.commit()

    print("\n" + "=" * 70)
    print(f"✅ Ingested {ok}/{len(representatives)} patients")
    print("=" * 70)
    print(f"  Patients:  {db.query(models.Patient).count()}")
    print(f"  Studies:   {db.query(models.Study).count()}")
    print(f"  Diagnostics: {db.query(models.DiagnosticAnalysis).count()}")
    print(f"  With previews: {db.query(models.ImageStatistics).filter(models.ImageStatistics.main_image_data.isnot(None)).count()}")
    print("\n🌐 http://localhost:3000\n")
    db.close()


if __name__ == "__main__":
    main()
