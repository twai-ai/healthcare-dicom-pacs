#!/usr/bin/env python3
"""
Upload showcase JSON/CSV and local DICOM files to S3-compatible storage.

Usage (from webapp/backend with env configured):
  python upload_showcase_to_storage.py

Requires S3_BUCKET and credentials. Skips keys that already exist.
"""

from pathlib import Path

from object_storage import (
    ANALYSIS_OUTPUT_LOCAL,
    ANALYSIS_PREFIX,
    DICOM_PREFIX,
    SHOWCASE_LOCAL,
    SHOWCASE_PREFIX,
    build_dicom_key,
    get_storage,
    normalize_dicom_key,
)

SHOWCASE_FILES = [
    "dicom_metadata.csv",
    "multimodel_ai_analysis_complete.json",
    "diagnostic_assessments_complete.json",
    "bias_analysis_report.json",
]


def upload_showcase_artifacts(storage) -> int:
    uploaded = 0
    for name in SHOWCASE_FILES:
        for base in (SHOWCASE_LOCAL, ANALYSIS_OUTPUT_LOCAL):
            path = base / name
            if not path.is_file():
                continue
            prefix = SHOWCASE_PREFIX if base == SHOWCASE_LOCAL else ANALYSIS_PREFIX
            key = f"{prefix}{name}"
            if storage.exists(key):
                print(f"  skip {key}")
                continue
            storage.put_file(key, path, content_type="application/octet-stream")
            print(f"  ✓ {key}")
            uploaded += 1
            break
    return uploaded


def upload_local_dicoms(storage) -> int:
    import pandas as pd

    uploaded = 0
    for csv_base in (SHOWCASE_LOCAL, ANALYSIS_OUTPUT_LOCAL):
        csv_path = csv_base / "dicom_metadata.csv"
        if not csv_path.is_file():
            continue
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            patient_id = row.get("patient_id") or row.get("PatientID")
            file_path = row.get("file_path")
            study_uid = row.get("study_instance_uid") or f"study-{patient_id}"
            if not patient_id or not file_path:
                continue
            key = normalize_dicom_key(str(file_path))
            if key and storage.exists(key):
                continue
            imported = storage.import_legacy_dicom(
                str(file_path), str(patient_id), str(study_uid)
            )
            if imported:
                print(f"  ✓ {imported}")
                uploaded += 1
        break
    return uploaded


def main():
    storage = get_storage()
    if not storage.use_s3:
        print("S3_BUCKET not set — nothing to upload (using local storage).")
        return

    print("Uploading showcase artifacts...")
    n1 = upload_showcase_artifacts(storage)
    print("Uploading DICOM files from metadata...")
    n2 = upload_local_dicoms(storage)
    print(f"\nDone. Uploaded {n1} artifacts and {n2} DICOM objects.")


if __name__ == "__main__":
    main()
