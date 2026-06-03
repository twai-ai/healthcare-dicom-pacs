"""
DICOM-AI Core — reproducible imaging analysis and evaluation.

Part of the ATRISI healthcare research ecosystem.
Prioritize: validation, reproducibility, structured observations (not diagnoses).
"""

from core.diagnostic_engine import DiagnosticEngine, ENGINE_VERSION
from core.schemas.findings import StructuredFindings

__all__ = ["DiagnosticEngine", "ENGINE_VERSION", "StructuredFindings"]
