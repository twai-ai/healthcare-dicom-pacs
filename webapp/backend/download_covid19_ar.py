#!/usr/bin/env python3
"""
Download missing TCIA COVID-19-AR patients into /data/raw/COVID-19-AR.

Prefers DX/CR series (single image) for faster ingest; falls back to smallest CT series.

Usage:
  python download_covid19_ar.py --target 80
  python download_covid19_ar.py --target 100 --max-download 90
"""

from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path
from typing import Optional, Set

import pandas as pd

try:
    from tcia_utils import nbia
except ImportError:
    raise SystemExit("Install tcia_utils: pip install tcia_utils")

COLLECTION = "COVID-19-AR"
DEFAULT_DIR = Path("/data/raw/COVID-19-AR")
_MODALITY_ORDER = ("DX", "CR", "CT")


def local_patient_ids(data_dir: Path) -> Set[str]:
    if not data_dir.is_dir():
        return set()
    return {
        p.name
        for p in data_dir.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    }


def pick_series_row(patient_series: pd.DataFrame) -> Optional[pd.Series]:
    for modality in _MODALITY_ORDER:
        subset = patient_series[patient_series["Modality"] == modality]
        if subset.empty:
            continue
        subset = subset.copy()
        subset["ImageCount"] = pd.to_numeric(
            subset.get("ImageCount", 1), errors="coerce"
        ).fillna(1)
        return subset.sort_values("ImageCount").iloc[0]
    return None


def download_patient_series(
    patient_id: str, series_uid: str, dest_root: Path
) -> int:
    patient_dir = dest_root / patient_id
    patient_dir.mkdir(parents=True, exist_ok=True)
    nbia.downloadSeries(
        series_data=[series_uid],
        path=str(patient_dir),
        input_type="list",
    )
    return len(list(patient_dir.rglob("*.dcm")))


def main() -> None:
    parser = argparse.ArgumentParser(description="Download TCIA COVID-19-AR cases")
    parser.add_argument(
        "--target",
        type=int,
        default=80,
        help="Total patients desired on disk (default: 80)",
    )
    parser.add_argument(
        "--max-download",
        type=int,
        default=0,
        help="Cap new downloads (0 = target minus current)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DIR,
        help="Output directory for patient folders",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds between TCIA requests",
    )
    args = parser.parse_args()

    args.data_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print(f"TCIA download: {COLLECTION} → {args.data_dir}")
    print("=" * 70)

    series_df = nbia.getSeries(collection=COLLECTION, format="df")
    if series_df is None or series_df.empty:
        raise SystemExit("No series returned from TCIA")

    local_ids = local_patient_ids(args.data_dir)
    all_ids = sorted(series_df["PatientID"].unique())
    missing_ids = [pid for pid in all_ids if pid not in local_ids]

    need = max(0, args.target - len(local_ids))
    cap = args.max_download if args.max_download > 0 else need
    to_fetch = missing_ids[: min(need, cap, len(missing_ids))]

    print(f"\nTCIA patients:     {len(all_ids)}")
    print(f"Already local:     {len(local_ids)}")
    print(f"Target total:      {args.target}")
    print(f"Will download:     {len(to_fetch)}")
    print(f"Remaining on TCIA: {len(missing_ids) - len(to_fetch)}")

    if not to_fetch:
        print("\n✓ Target already met — nothing to download.")
        return

    ok = 0
    failed = []

    for idx, patient_id in enumerate(to_fetch, 1):
        patient_series = series_df[series_df["PatientID"] == patient_id]
        row = pick_series_row(patient_series)
        if row is None:
            print(f"\n[{idx}/{len(to_fetch)}] {patient_id} — no series, skip")
            failed.append(patient_id)
            continue

        uid = row["SeriesInstanceUID"]
        modality = row["Modality"]
        images = row.get("ImageCount", "?")

        print(
            f"\n[{idx}/{len(to_fetch)}] {patient_id} — {modality} "
            f"({images} image(s))"
        )

        try:
            count = download_patient_series(patient_id, uid, args.data_dir)
            if count:
                print(f"  ✓ {count} DICOM file(s) → {args.data_dir / patient_id}")
                ok += 1
            else:
                print("  ✗ No .dcm files after download")
                failed.append(patient_id)
        except Exception as exc:
            print(f"  ✗ {exc}")
            failed.append(patient_id)

        time.sleep(args.delay)

    # Cleanup test folder if present
    test_dir = args.data_dir / "_test_download"
    if test_dir.is_dir():
        shutil.rmtree(test_dir, ignore_errors=True)

    final_count = len(local_patient_ids(args.data_dir))
    print("\n" + "=" * 70)
    print(f"✅ Downloaded {ok}/{len(to_fetch)} patients")
    print(f"   Total on disk: {final_count} patients")
    if failed:
        print(f"   Failed/skipped: {len(failed)}")
    print("=" * 70)
    print("\nNext: docker exec dicom-ai-backend python process_all_covid_data.py\n")


if __name__ == "__main__":
    main()
