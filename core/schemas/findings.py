"""Canonical structured findings — observations, not diagnoses."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0.0"


class FindingPolarity(str, Enum):
    present = "present"
    absent = "absent"
    indeterminate = "indeterminate"


class ClinicalFinding(BaseModel):
    code: str
    category: str = "pattern"
    description: str
    polarity: FindingPolarity = FindingPolarity.indeterminate
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    source: str = "heuristic_engine"
    evidence: Dict[str, Any] = Field(default_factory=dict)


class ReasoningStep(BaseModel):
    rule_id: str
    fired: bool
    delta_score: int = 0
    detail: Optional[str] = None


class ObservationPrediction(BaseModel):
    """Engine observation summary — not a clinical diagnosis."""

    pattern_score: int = Field(..., ge=0, le=5)
    pattern_score_max: int = 5
    pattern_label: str
    severity_observation: str
    confidence: str
    supporting_features: List[str] = Field(default_factory=list)


class StructuredFindings(BaseModel):
    schema_version: str = SCHEMA_VERSION
    engine_version: str
    study_instance_uid: str
    patient_id: str
    analyzed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    modality: str = "Unknown"
    task: str = "covid19_cxr_screening"

    quantitative_features: Dict[str, Any] = Field(default_factory=dict)
    observations: ObservationPrediction
    clinical_findings: List[ClinicalFinding] = Field(default_factory=list)
    differential_considerations: List[str] = Field(default_factory=list)
    suggested_follow_up: List[str] = Field(default_factory=list)
    reasoning_trace: List[ReasoningStep] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)

    disclaimer: str = (
        "Automated imaging observations for research and evaluation. "
        "Not a clinical diagnosis. Requires qualified physician interpretation."
    )

    def legacy_diagnostic_dict(self) -> Dict[str, Any]:
        """Map to existing DB columns during migration."""
        obs = self.observations
        return {
            "covid_score": obs.pattern_score,
            "covid_probability": obs.pattern_label,
            "severity": obs.severity_observation,
            "confidence": obs.confidence,
            "clinical_reasoning": "; ".join(
                f.description for f in self.clinical_findings[:5]
            )
            or "Quantitative pattern analysis completed.",
            "recommendations": "; ".join(self.suggested_follow_up[:3]),
            "quantitative_features": self.quantitative_features,
            "findings_json": self.model_dump(mode="json"),
        }
