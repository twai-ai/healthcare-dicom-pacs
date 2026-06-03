"""Parse free-text AI reports into structured observation labels for agreement."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional


def parse_pattern_label_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    lower = text.lower()
    if re.search(r"\b(negative|no clear|unlikely|low probability|not suggest)\b", lower):
        return "LOW_PATTERN_SIMILARITY"
    if re.search(r"\b(indeterminate|equivocal|possible|moderate|uncertain)\b", lower):
        return "MODERATE_PATTERN_SIMILARITY"
    if re.search(r"\b(positive|high probability|typical|consistent with covid|suggestive)\b", lower):
        return "HIGH_PATTERN_SIMILARITY"
    return None


def parse_severity_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    lower = text.lower()
    if "severe" in lower:
        return "moderate-to-extensive"
    if "mild" in lower:
        return "limited"
    if "moderate" in lower:
        return "limited"
    return None


def label_to_score(label: Optional[str]) -> Optional[int]:
    if not label:
        return None
    if "LOW" in label:
        return 1
    if "MODERATE" in label:
        return 3
    if "HIGH" in label:
        return 4
    return None


def parse_ai_analysis(text: str, source: str) -> Dict[str, Any]:
    pattern = parse_pattern_label_from_text(text)
    return {
        "finding": "ai_pattern_interpretation",
        "pattern_label": pattern,
        "pattern_score": label_to_score(pattern),
        "severity_observation": parse_severity_from_text(text),
        "confidence": None,
        "source": source,
        "raw_excerpt": text[:500] if text else "",
    }
