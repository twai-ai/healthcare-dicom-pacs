from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DatasetRecord(BaseModel):
    id: str
    name: str
    version: str
    source: str = "tcia"
    collection_id: Optional[str] = None
    task: str = "covid19_cxr_screening"
    manifest: str
    ground_truth: Optional[str] = None
    modalities: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class DatasetManifestEntry(BaseModel):
    study_instance_uid: str
    patient_id: str
    dicom_path: str
    split: str = "all"
    modality: Optional[str] = None
    manufacturer: Optional[str] = None
