#!/usr/bin/env python3
"""Scan data/ for DICOM files and rebuild dataset manifest with real UIDs."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.dicom_io import find_dicom_files, metadata_from_dataset, read_dicom

MANIFEST_OUT = Path(__file__).parent / "manifests" / "covid19_tcia_showcase.csv"


def main():
    parser = argparse.ArgumentParser(description="Build TCIA showcase manifest from data/")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=REPO_ROOT / "data",
        help="Root directory to scan for DICOM",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MANIFEST_OUT,
        help="Output manifest CSV path",
    )
    args = parser.parse_args()

    files = find_dicom_files(args.data_dir)
    if not files:
        print(f"No DICOM files under {args.data_dir}")
        return 1

    rows = []
    for dcm in sorted(files):
        ds = read_dicom(dcm)
        meta = metadata_from_dataset(ds)
        try:
            rel = dcm.relative_to(REPO_ROOT)
        except ValueError:
            rel = dcm
        rows.append(
            {
                "study_instance_uid": meta["study_instance_uid"],
                "patient_id": meta["patient_id"],
                "dicom_path": str(rel).replace("\\", "/"),
                "split": "test",
                "modality": meta.get("modality", ""),
                "manufacturer": meta.get("manufacturer", ""),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "study_instance_uid",
                "patient_id",
                "dicom_path",
                "split",
                "modality",
                "manufacturer",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
