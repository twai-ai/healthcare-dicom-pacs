"""
Unified heuristic analysis engine — single source of truth for rule-based observations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pydicom

from core.dicom_io import metadata_from_dataset, parse_age_years, read_dicom
from core.feature_extractor import extract_quantitative_features
from core.schemas.findings import (
    ClinicalFinding,
    FindingPolarity,
    ObservationPrediction,
    ReasoningStep,
    StructuredFindings,
)

ENGINE_VERSION = "1.0.0"


class DiagnosticEngine:
    """Produces StructuredFindings (observations) from DICOM inputs."""

    def __init__(self, engine_version: str = ENGINE_VERSION):
        self.engine_version = engine_version

    def analyze(
        self,
        dicom_source: Union[Path, str, pydicom.Dataset],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StructuredFindings:
        if isinstance(dicom_source, pydicom.Dataset):
            ds = dicom_source
        else:
            ds = read_dicom(Path(dicom_source))

        meta = metadata or metadata_from_dataset(ds)
        features = extract_quantitative_features(ds)
        return self._build_findings(ds, meta, features)

    def analyze_path(self, dicom_path: Path) -> StructuredFindings:
        return self.analyze(dicom_path)

    def _build_findings(
        self,
        ds: pydicom.Dataset,
        metadata: Dict[str, Any],
        features: Dict[str, Any],
    ) -> StructuredFindings:
        study_uid = str(
            metadata.get("study_instance_uid") or ds.get("StudyInstanceUID", "")
        )
        patient_id = str(metadata.get("patient_id", "Unknown"))

        findings_text: List[str] = []
        assumptions: List[str] = []
        clinical_findings: List[ClinicalFinding] = []
        reasoning_trace: List[ReasoningStep] = []
        score = 0

        age_years = metadata.get("patient_age_years")
        if age_years is None:
            age_years = parse_age_years(metadata.get("patient_age"))

        if age_years and age_years > 60:
            findings_text.append(
                f"Age {age_years}Y — demographic factor noted in published COVID-19 risk literature"
            )
            assumptions.append("Age used only as epidemiological context, not diagnosis")

        if metadata.get("patient_sex") == "M":
            findings_text.append("Male sex — epidemiological context only")

        study_desc = str(metadata.get("study_description", "")).upper()
        if "PORTABLE" in study_desc or " AP" in study_desc:
            clinical_findings.append(
                ClinicalFinding(
                    code="portable_ap_view",
                    category="technique",
                    description="Portable AP technique — may limit fine detail assessment",
                    polarity=FindingPolarity.present,
                    source="metadata",
                )
            )

        if features:
            cv = features.get("coefficient_of_variation", 0)
            if cv > 0.5:
                clinical_findings.append(
                    ClinicalFinding(
                        code="high_parenchymal_heterogeneity",
                        category="pattern",
                        description="High intensity variation across the field",
                        polarity=FindingPolarity.present,
                        confidence=min(0.9, 0.5 + cv / 2),
                        source="heuristic_engine",
                        evidence={"coefficient_of_variation": cv},
                    )
                )
                findings_text.append(
                    f"Heterogeneous parenchymal intensity (CV={cv:.2f})"
                )

            asym = features.get("bilateral_asymmetry", 1.0)
            if asym < 0.15:
                step = ReasoningStep(
                    rule_id="bilateral_symmetry_low_asymmetry",
                    fired=True,
                    delta_score=2,
                    detail=f"bilateral_asymmetry={asym:.3f}",
                )
                reasoning_trace.append(step)
                score += 2
                clinical_findings.append(
                    ClinicalFinding(
                        code="bilateral_symmetric_pattern",
                        category="pattern",
                        description="Relatively symmetric bilateral density pattern",
                        polarity=FindingPolarity.present,
                        confidence=0.7,
                        source="heuristic_engine",
                        evidence={"bilateral_asymmetry": asym},
                    )
                )
            else:
                reasoning_trace.append(
                    ReasoningStep(
                        rule_id="bilateral_symmetry_low_asymmetry",
                        fired=False,
                        delta_score=0,
                    )
                )

            if features.get("lower_field_heterogeneity"):
                reasoning_trace.append(
                    ReasoningStep(
                        rule_id="lower_field_heterogeneity",
                        fired=True,
                        delta_score=1,
                    )
                )
                score += 1
                clinical_findings.append(
                    ClinicalFinding(
                        code="lower_field_heterogeneity",
                        category="pattern",
                        description="Increased heterogeneity in lower lung zones",
                        polarity=FindingPolarity.present,
                        source="heuristic_engine",
                    )
                )
            else:
                reasoning_trace.append(
                    ReasoningStep(
                        rule_id="lower_field_heterogeneity",
                        fired=False,
                        delta_score=0,
                    )
                )

            if cv > 0.4:
                reasoning_trace.append(
                    ReasoningStep(
                        rule_id="cv_elevated",
                        fired=True,
                        delta_score=1,
                        detail=f"cv={cv:.2f}",
                    )
                )
                score += 1
            else:
                reasoning_trace.append(
                    ReasoningStep(rule_id="cv_elevated", fired=False, delta_score=0)
                )

        if age_years and age_years > 50:
            reasoning_trace.append(
                ReasoningStep(
                    rule_id="age_gt_50_context",
                    fired=True,
                    delta_score=1,
                    detail=f"age={age_years}",
                )
            )
            score += 1
        else:
            reasoning_trace.append(
                ReasoningStep(rule_id="age_gt_50_context", fired=False, delta_score=0)
            )

        score = min(score, 5)
        supporting = [s.rule_id for s in reasoning_trace if s.fired]

        if score >= 4:
            pattern_label = "HIGH_PATTERN_SIMILARITY"
            confidence = "high"
        elif score >= 2:
            pattern_label = "MODERATE_PATTERN_SIMILARITY"
            confidence = "moderate"
        else:
            pattern_label = "LOW_PATTERN_SIMILARITY"
            confidence = "low"

        severity = self._severity_observation(score, features)
        differential = self._differential(metadata, features, score)
        follow_up = self._follow_up(pattern_label, metadata)

        return StructuredFindings(
            engine_version=self.engine_version,
            study_instance_uid=study_uid,
            patient_id=patient_id,
            modality=str(metadata.get("modality", ds.get("Modality", "Unknown"))),
            quantitative_features=features,
            observations=ObservationPrediction(
                pattern_score=score,
                pattern_score_max=5,
                pattern_label=pattern_label,
                severity_observation=severity,
                confidence=confidence,
                supporting_features=supporting,
            ),
            clinical_findings=clinical_findings,
            differential_considerations=differential,
            suggested_follow_up=follow_up,
            reasoning_trace=reasoning_trace,
            assumptions=assumptions,
            data_sources=["metadata", "image_statistics", "technical_parameters"],
        )

    def _severity_observation(self, score: int, features: Dict[str, Any]) -> str:
        if score < 2:
            return "No substantial pattern signal for severity estimation"
        heterogeneity = features.get("coefficient_of_variation", 0)
        lower = features.get("lower_field_heterogeneity", False)
        sev = 0
        if heterogeneity > 0.6:
            sev += 2
        elif heterogeneity > 0.4:
            sev += 1
        if lower:
            sev += 1
        if sev >= 3:
            return "Observed extent suggests moderate-to-extensive parenchymal involvement"
        if sev >= 1:
            return "Observed extent suggests limited parenchymal involvement"
        return "Minimal observed parenchymal signal"

    def _differential(
        self, metadata: Dict[str, Any], features: Dict[str, Any], score: int
    ) -> List[str]:
        items: List[str] = []
        if score >= 2:
            items.append("Viral pneumonia pattern (literature-associated with COVID-19)")
        age_years = metadata.get("patient_age_years") or parse_age_years(
            metadata.get("patient_age")
        )
        if age_years and age_years > 60:
            items.extend(
                [
                    "Bacterial pneumonia (consider in differential)",
                    "Cardiogenic pulmonary edema (consider in differential)",
                ]
            )
        if score < 2:
            items.insert(0, "No acute pattern signal on automated observation")
        return items[:5]

    def _follow_up(self, pattern_label: str, metadata: Dict[str, Any]) -> List[str]:
        base = [
            "Correlate with clinical presentation and laboratory data",
            "Formal radiological interpretation by a qualified physician",
        ]
        if "HIGH" in pattern_label:
            base.insert(
                0,
                "Consider additional imaging or testing per institutional protocol if clinically indicated",
            )
        elif "MODERATE" in pattern_label:
            base.insert(
                0,
                "Consider follow-up imaging if symptoms persist (observational recommendation only)",
            )
        if "PORTABLE" in str(metadata.get("study_description", "")).upper():
            base.append(
                "Repeat standard PA/lateral views when feasible for technical comparison"
            )
        return base
