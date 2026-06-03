"""DICOM read helpers shared across analysis and evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pydicom


def find_dicom_files(directory: Path, recursive: bool = True) -> List[Path]:
    pattern = "**/*" if recursive else "*"
    found: List[Path] = []
    for file in directory.glob(pattern):
        if not file.is_file() or file.name.startswith("."):
            continue
        try:
            pydicom.dcmread(file, stop_before_pixels=True)
            found.append(file)
        except Exception:
            continue
    return found


def read_dicom(file_path: Path) -> pydicom.Dataset:
    return pydicom.dcmread(file_path)


def parse_age_years(age_value: Any) -> Optional[int]:
    if age_value is None or age_value == "":
        return None
    s = str(age_value).strip()
    if not s or s == "Unknown":
        return None
    try:
        if "Y" in s.upper():
            return int(s.upper().replace("Y", "").strip())
        return int(float(s))
    except (TypeError, ValueError):
        return None


def metadata_from_dataset(ds: pydicom.Dataset) -> Dict[str, Any]:
    age_raw = ds.get("PatientAge", "")
    age_years = parse_age_years(age_raw)

    meta: Dict[str, Any] = {
        "patient_id": str(ds.get("PatientID", "Unknown")),
        "patient_name": str(ds.get("PatientName", "Unknown")),
        "patient_age": age_years if age_years is not None else str(age_raw or "Unknown"),
        "patient_age_years": age_years,
        "patient_sex": str(ds.get("PatientSex", "Unknown")),
        "study_date": str(ds.get("StudyDate", "")),
        "study_time": str(ds.get("StudyTime", "")),
        "study_description": str(ds.get("StudyDescription", "Unknown")),
        "series_description": str(ds.get("SeriesDescription", "Unknown")),
        "modality": str(ds.get("Modality", "Unknown")),
        "body_part": str(ds.get("BodyPartExamined", "")),
        "manufacturer": str(ds.get("Manufacturer", "Unknown")),
        "manufacturer_model": str(ds.get("ManufacturerModelName", "")),
        "institution": str(ds.get("InstitutionName", "Unknown")),
        "study_instance_uid": str(ds.get("StudyInstanceUID", "")),
        "series_instance_uid": str(ds.get("SeriesInstanceUID", "")),
        "sop_instance_uid": str(ds.get("SOPInstanceUID", "")),
    }

    if hasattr(ds, "Rows"):
        meta["rows"] = int(ds.Rows)
        meta["columns"] = int(ds.Columns)
        meta["bits_stored"] = ds.get("BitsStored")
        meta["pixel_spacing"] = str(ds.get("PixelSpacing", "Unknown"))

    if hasattr(ds, "pixel_array"):
        import numpy as np

        arr = ds.pixel_array.astype(float)
        meta["image_stats"] = {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "median": float(np.median(arr)),
        }

    return meta
