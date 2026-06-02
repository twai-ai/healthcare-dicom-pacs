"""
Resolve environment variables for Railway Postgres and Storage Buckets.

Railway injects bucket credentials as BUCKET, ENDPOINT, ACCESS_KEY_ID, etc.
or AWS_* presets when using variable references from the bucket service.
"""

from __future__ import annotations

import os
from typing import Optional


def _first(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def resolve_database_url() -> str:
    return _first("DATABASE_URL", "DATABASE_PRIVATE_URL") or (
        "postgresql://dicom_user:dicom_pass_2024@localhost:5432/dicom_ai"
    )


def resolve_s3_bucket() -> str:
    return _first("S3_BUCKET", "AWS_S3_BUCKET_NAME", "BUCKET")


def resolve_s3_endpoint() -> Optional[str]:
    return _first("S3_ENDPOINT_URL", "AWS_ENDPOINT_URL", "ENDPOINT") or None


def resolve_s3_region() -> str:
    return _first("S3_REGION", "AWS_DEFAULT_REGION", "REGION") or "auto"


def resolve_aws_access_key() -> Optional[str]:
    return _first("AWS_ACCESS_KEY_ID", "ACCESS_KEY_ID") or None


def resolve_aws_secret_key() -> Optional[str]:
    return _first("AWS_SECRET_ACCESS_KEY", "SECRET_ACCESS_KEY") or None


def s3_addressing_style() -> str:
    """Railway buckets default to virtual-hosted style."""
    style = _first("AWS_S3_URL_STYLE", "S3_ADDRESSING_STYLE").lower()
    if style in ("path", "virtual"):
        return style
    endpoint = resolve_s3_endpoint() or ""
    if "storage.railway.app" in endpoint:
        return "virtual"
    return "path"


def is_railway_bucket(endpoint: Optional[str]) -> bool:
    return bool(endpoint and "storage.railway.app" in endpoint)
