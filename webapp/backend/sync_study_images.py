"""CLI: populate scan preview images for all studies."""

from database import SessionLocal
from study_images import sync_all_study_images


def main():
    db = SessionLocal()
    try:
        sync_all_study_images(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
