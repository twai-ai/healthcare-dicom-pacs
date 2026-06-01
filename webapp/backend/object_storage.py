"""
S3-compatible object storage with local filesystem fallback.

Production: set S3_BUCKET (+ credentials / S3_ENDPOINT_URL for R2 or MinIO).
Development: omit S3_BUCKET to use LOCAL_STORAGE_ROOT (default /data/raw).
"""

from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator, List, Optional, Union
from urllib.parse import urlparse

# Object key prefixes inside the bucket (or under LOCAL_STORAGE_ROOT)
DICOM_PREFIX = os.getenv("S3_DICOM_PREFIX", "dicom/")
SHOWCASE_PREFIX = os.getenv("S3_SHOWCASE_PREFIX", "showcase/")
ANALYSIS_PREFIX = os.getenv("S3_ANALYSIS_PREFIX", "analysis/")

LOCAL_ROOT = Path(os.getenv("LOCAL_STORAGE_ROOT", "/data/raw"))
SHOWCASE_LOCAL = Path(os.getenv("SHOWCASE_DATA_DIR", "/showcase_data"))
ANALYSIS_OUTPUT_LOCAL = Path(os.getenv("ANALYSIS_OUTPUT_DIR", "/analysis_output"))


def storage_enabled() -> bool:
    """True when S3_BUCKET is configured."""
    return bool(os.getenv("S3_BUCKET", "").strip())


def get_storage_backend() -> str:
    return "s3" if storage_enabled() else "local"


def normalize_dicom_key(path_or_key: Optional[str]) -> Optional[str]:
    """
    Convert legacy host paths or s3:// URIs to a canonical object key under dicom/.
    Keys already starting with dicom/ are returned unchanged.
    """
    if not path_or_key or str(path_or_key).strip() in ("", "Unknown", "nan"):
        return None

    raw = str(path_or_key).strip().replace("\\", "/")

    if raw.startswith("s3://"):
        parsed = urlparse(raw)
        # s3://bucket/key -> key
        key = parsed.path.lstrip("/")
        if key.startswith(DICOM_PREFIX):
            return key
        return f"{DICOM_PREFIX}{key.lstrip('/')}"

    if raw.startswith(DICOM_PREFIX):
        return raw

    markers = (
        "/data/raw/",
        f"{LOCAL_ROOT.as_posix()}/",
        "/DICOM-AI/data/raw/",
        "data/raw/",
    )
    for marker in markers:
        if marker in raw:
            rel = raw.split(marker, 1)[1].lstrip("/")
            return f"{DICOM_PREFIX}{rel}"

    path = Path(raw)
    if path.is_absolute() and path.exists():
        try:
            rel = path.resolve().relative_to(LOCAL_ROOT.resolve())
            return f"{DICOM_PREFIX}{rel.as_posix()}"
        except ValueError:
            pass

    if raw.endswith(".dcm") and "/" not in raw:
        return f"{DICOM_PREFIX}{raw}"

    return raw


def build_dicom_key(patient_id: str, study_instance_uid: str, filename: str) -> str:
    safe_uid = "".join(c if c.isalnum() or c in ".-_" else "_" for c in study_instance_uid)
    safe_name = Path(filename).name or "upload.dcm"
    safe_patient = "".join(
        c if c.isalnum() or c in ".-_" else "_" for c in (patient_id or "unknown")
    )
    return f"{DICOM_PREFIX}{safe_patient}/{safe_uid}/{safe_name}"


class ObjectStorage:
    def __init__(self) -> None:
        self._client = None
        self.bucket = os.getenv("S3_BUCKET", "").strip()
        self.region = os.getenv("S3_REGION", os.getenv("AWS_DEFAULT_REGION", "auto"))
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL") or None

    @property
    def use_s3(self) -> bool:
        return bool(self.bucket)

    def _get_client(self):
        if self._client is None:
            import boto3

            session = boto3.session.Session()
            self._client = session.client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            )
        return self._client

    def _local_path(self, key: str) -> Path:
        if key.startswith(DICOM_PREFIX):
            rel = key[len(DICOM_PREFIX) :]
        elif key.startswith(SHOWCASE_PREFIX):
            rel = f"_showcase/{key[len(SHOWCASE_PREFIX) :]}"
        elif key.startswith(ANALYSIS_PREFIX):
            rel = f"_analysis/{key[len(ANALYSIS_PREFIX) :]}"
        else:
            rel = key
        return LOCAL_ROOT / rel

    def exists(self, key: str) -> bool:
        if self.use_s3:
            try:
                self._get_client().head_object(Bucket=self.bucket, Key=key)
                return True
            except Exception:
                return False
        return self._local_path(key).is_file()

    def put_file(self, key: str, source: Union[Path, str], content_type: str = "application/dicom") -> str:
        source_path = Path(source)
        if self.use_s3:
            extra = {"ContentType": content_type}
            self._get_client().upload_file(
                str(source_path), self.bucket, key, ExtraArgs=extra
            )
            return key

        dest = self._local_path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source_path.read_bytes())
        return key

    def put_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        if self.use_s3:
            self._get_client().put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            return key

        dest = self._local_path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return key

    def list_keys(self, prefix: str) -> List[str]:
        if self.use_s3:
            keys: List[str] = []
            paginator = self._get_client().get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    k = obj["Key"]
                    if k.lower().endswith(".dcm"):
                        keys.append(k)
            return keys

        base = self._local_path(prefix if prefix.startswith(DICOM_PREFIX) else prefix)
        if not base.exists():
            # list under LOCAL_ROOT for dicom prefix
            root = LOCAL_ROOT
            if prefix.startswith(DICOM_PREFIX):
                root = LOCAL_ROOT / prefix[len(DICOM_PREFIX) :]
            if not root.exists():
                return []
            base = root

        if base.is_file():
            return [prefix]
        return [f"{DICOM_PREFIX}{p.relative_to(LOCAL_ROOT).as_posix()}" for p in base.rglob("*.dcm")]

    @contextmanager
    def open_local_copy(self, key: str) -> Iterator[Path]:
        """Yield a local path to object bytes (temp file for S3)."""
        if self.use_s3:
            suffix = Path(key).suffix or ".dcm"
            fd, tmp_name = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
            tmp = Path(tmp_name)
            try:
                self._get_client().download_file(self.bucket, key, str(tmp))
                yield tmp
            finally:
                if tmp.exists():
                    tmp.unlink()
        else:
            path = self._local_path(key)
            if not path.is_file():
                raise FileNotFoundError(f"Local object not found: {key} -> {path}")
            yield path

    def import_legacy_dicom(self, legacy_path: str, patient_id: str, study_uid: str) -> Optional[str]:
        """
        If legacy_path points to a local file, upload/copy to canonical key.
        Returns canonical key or None.
        """
        key = normalize_dicom_key(legacy_path)
        if not key:
            return None

        if self.exists(key):
            return key

        resolved = _resolve_local_legacy_path(legacy_path)
        if resolved and resolved.is_file():
            filename = resolved.name
            canonical = build_dicom_key(patient_id, study_uid, filename)
            return self.put_file(canonical, resolved)

        return key if self.exists(key) else None


def find_local_dicom_path(patient_id: str, hint_path: Optional[str] = None) -> Optional[Path]:
    """Search LOCAL_ROOT for a patient's DICOM (dev / docker volume)."""
    if hint_path:
        resolved = _resolve_local_legacy_path(hint_path)
        if resolved:
            return resolved

    patient_dir = LOCAL_ROOT / "COVID-19-AR" / patient_id
    if patient_dir.is_dir():
        for dcm in sorted(patient_dir.rglob("*.dcm")):
            return dcm

    if LOCAL_ROOT.is_dir():
        for dcm in LOCAL_ROOT.rglob("*.dcm"):
            if patient_id in dcm.parts:
                return dcm
    return None


def _resolve_local_legacy_path(file_path: str) -> Optional[Path]:
    key = normalize_dicom_key(file_path)
    if not key:
        return None

    candidates = [Path(file_path.strip())]
    if key.startswith(DICOM_PREFIX):
        candidates.append(LOCAL_ROOT / key[len(DICOM_PREFIX) :])

    for marker in ("/data/raw/", "data/raw/", "/DICOM-AI/data/raw/"):
        if marker in file_path:
            candidates.append(LOCAL_ROOT / file_path.split(marker, 1)[1])

    for candidate in candidates:
        if candidate.is_file() and candidate.suffix.lower() == ".dcm":
            return candidate
    return None


@contextmanager
def open_data_file(
    filename: str,
    *,
    local_dirs: Optional[List[Path]] = None,
    s3_keys: Optional[List[str]] = None,
) -> Iterator[Path]:
    """
    Open a showcase/analysis data file from local dirs or S3 (downloaded to temp).
    """
    dirs = local_dirs or [SHOWCASE_LOCAL, ANALYSIS_OUTPUT_LOCAL]
    keys = s3_keys or [
        f"{SHOWCASE_PREFIX}{filename}",
        f"{ANALYSIS_PREFIX}{filename}",
    ]

    for directory in dirs:
        path = directory / filename
        if path.is_file():
            yield path
            return

    storage = get_storage()
    if storage.use_s3:
        for key in keys:
            if storage.exists(key):
                with storage.open_local_copy(key) as tmp:
                    yield tmp
                return

    raise FileNotFoundError(
        f"Data file '{filename}' not found in {dirs} or S3 keys {keys}"
    )


_storage: Optional[ObjectStorage] = None


def get_storage() -> ObjectStorage:
    global _storage
    if _storage is None:
        _storage = ObjectStorage()
    return _storage
