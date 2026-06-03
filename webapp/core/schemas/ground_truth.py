from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class GroundTruthLabel(BaseModel):
    study_instance_uid: str
    patient_id: Optional[str] = None
    pattern_score_gt: Optional[int] = Field(None, ge=0, le=5)
    pattern_label_gt: Optional[str] = None
    severity_gt: Optional[str] = None
    covid_label: Optional[str] = None
    reader_id: Optional[str] = None
    source: str = "manual"
    provenance: Dict[str, Any] = Field(default_factory=dict)
