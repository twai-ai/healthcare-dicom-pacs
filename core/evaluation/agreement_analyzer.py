"""Agreement between engine, ground truth, and optional AI outputs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.evaluation.metrics import label_to_score, summarize_scores
from core.schemas.findings import StructuredFindings
from core.schemas.ground_truth import GroundTruthLabel


def compare_engine_to_ground_truth(
    findings_list: List[StructuredFindings],
    labels: Dict[str, GroundTruthLabel],
) -> Dict[str, Any]:
    pred_scores: List[int] = []
    gt_scores: List[int] = []
    mismatches: List[Dict[str, Any]] = []

    for f in findings_list:
        uid = f.study_instance_uid
        if uid not in labels or labels[uid].pattern_score_gt is None:
            continue
        p = f.observations.pattern_score
        g = labels[uid].pattern_score_gt
        pred_scores.append(p)
        gt_scores.append(g)
        if p != g:
            mismatches.append(
                {
                    "study_instance_uid": uid,
                    "patient_id": f.patient_id,
                    "predicted_score": p,
                    "ground_truth_score": g,
                    "predicted_label": f.observations.pattern_label,
                    "ground_truth_label": labels[uid].pattern_label_gt,
                }
            )

    metrics = summarize_scores(pred_scores, gt_scores)
    return {
        "comparison": "engine_vs_ground_truth",
        "metrics": metrics,
        "mismatches": mismatches,
    }


def compare_labels_to_ground_truth(
    parsed_ai: List[Dict[str, Any]],
    labels: Dict[str, GroundTruthLabel],
    study_uids: List[str],
    model_name: str,
) -> Dict[str, Any]:
    pred_scores: List[int] = []
    gt_scores: List[int] = []

    for uid, parsed in zip(study_uids, parsed_ai):
        if uid not in labels or labels[uid].pattern_score_gt is None:
            continue
        score = parsed.get("pattern_score")
        if score is None:
            label = parsed.get("pattern_label")
            score = label_to_score(label) if label else None
        if score is None:
            continue
        pred_scores.append(int(score))
        gt_scores.append(int(labels[uid].pattern_score_gt))

    metrics = summarize_scores(pred_scores, gt_scores)
    rate = metrics.get("exact_score_match_rate")
    pct = f"{rate * 100:.1f}%" if rate is not None else "N/A"
    return {
        "comparison": f"{model_name}_vs_ground_truth",
        "agreement_display": pct,
        "metrics": metrics,
        "n_paired": len(pred_scores),
    }


def full_agreement_report(
    engine_vs_gt: Dict[str, Any],
    ai_comparisons: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "engine_vs_ground_truth": engine_vs_gt,
        "ai_vs_ground_truth": ai_comparisons,
    }
