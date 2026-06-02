"""
Startup bootstrap for Railway: sync showcase files to bucket, seed DB if empty.
"""

from __future__ import annotations

import os

from database import SessionLocal
import models
from object_storage import SHOWCASE_PREFIX, get_storage, open_data_file

SHOWCASE_FILES = (
    "dicom_metadata.csv",
    "multimodel_ai_analysis_complete.json",
    "diagnostic_assessments_complete.json",
    "bias_analysis_report.json",
)


def _bootstrap_enabled() -> bool:
    return os.getenv("AUTO_BOOTSTRAP", "true").lower() in ("1", "true", "yes")


def sync_showcase_to_bucket() -> int:
    """Upload bundled /showcase_data files to object storage if missing."""
    from object_storage import SHOWCASE_LOCAL

    storage = get_storage()
    if not storage.use_s3:
        return 0

    uploaded = 0
    for name in SHOWCASE_FILES:
        key = f"{SHOWCASE_PREFIX}{name}"
        if storage.exists(key):
            continue
        local = SHOWCASE_LOCAL / name
        if not local.is_file():
            continue
        storage.put_file(key, local, content_type="application/octet-stream")
        print(f"  ✓ Uploaded showcase/{name}")
        uploaded += 1
    return uploaded


def seed_database_if_empty() -> bool:
    """Load showcase patients into Postgres when the database has no patients."""
    db = SessionLocal()
    try:
        if db.query(models.Patient).count() > 0:
            print("  ℹ Database already has patients — skip seed")
            return False

        try:
            with open_data_file("dicom_metadata.csv"):
                pass
        except FileNotFoundError:
            print("  ⚠ No dicom_metadata.csv in bucket or /showcase_data — skip seed")
            return False

        print("  → Loading showcase data into Postgres...")
        from comprehensive_data_loader import (
            load_ai_analyses,
            load_bias_and_metrics,
            load_diagnostics,
            load_patients,
        )
        from study_images import sync_all_study_images

        load_patients(db)
        load_ai_analyses(db)
        load_diagnostics(db)
        load_bias_and_metrics(db)
        sync_all_study_images(db)
        print(
            f"  ✓ Seeded {db.query(models.Patient).count()} patients, "
            f"{db.query(models.Study).count()} studies"
        )
        return True
    except Exception as exc:
        print(f"  ✗ Bootstrap seed failed: {exc}")
        db.rollback()
        return False
    finally:
        db.close()


def run_bootstrap() -> None:
    if not _bootstrap_enabled():
        print("AUTO_BOOTSTRAP disabled — skipping startup bootstrap")
        return

    print("Running startup bootstrap...")
    sync_showcase_to_bucket()
    seed_database_if_empty()
    print("Bootstrap complete.")


if __name__ == "__main__":
    run_bootstrap()
