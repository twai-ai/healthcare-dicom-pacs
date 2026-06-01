"""CLI: populate scan preview images for all studies."""

from pathlib import Path

from database import SessionLocal
from study_images import sync_all_study_images

METADATA_CANDIDATES = [
    Path("/showcase_data/dicom_metadata.csv"),
    Path("/analysis_output/dicom_metadata.csv"),
]


def main():
    db = SessionLocal()
    try:
        metadata = next((p for p in METADATA_CANDIDATES if p.exists()), None)
        sync_all_study_images(db, metadata)
    finally:
        db.close()


if __name__ == "__main__":
    main()
