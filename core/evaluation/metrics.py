"""Classification metrics for pattern-score evaluation."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np


def exact_match_rate(pred: List[int], gt: List[int]) -> float:
    if not pred:
        return 0.0
    return float(np.mean([p == g for p, g in zip(pred, gt)]))


def mean_absolute_error(pred: List[int], gt: List[int]) -> float:
    if not pred:
        return 0.0
    return float(np.mean([abs(p - g) for p, g in zip(pred, gt)]))


def quadratic_weighted_kappa(pred: List[int], gt: List[int], min_rating: int = 0, max_rating: int = 5) -> Optional[float]:
    if len(pred) < 2:
        return None
    try:
        from sklearn.metrics import cohen_kappa_score

        return float(
            cohen_kappa_score(gt, pred, weights="quadratic", labels=list(range(min_rating, max_rating + 1)))
        )
    except Exception:
        return None


def cohen_kappa_binary(pred_bin: List[int], gt_bin: List[int]) -> Optional[float]:
    if len(pred_bin) < 2 or len(set(gt_bin)) < 2:
        return None
    try:
        from sklearn.metrics import cohen_kappa_score

        return float(cohen_kappa_score(gt_bin, pred_bin))
    except Exception:
        return None


def collapse_high(score: int, threshold: int = 2) -> int:
    return 1 if score > threshold else 0


def confusion_counts(pred: List[int], gt: List[int], labels: List[int]) -> Dict[str, Dict[str, int]]:
    matrix: Dict[str, Dict[str, int]] = {str(l): {str(l2): 0 for l2 in labels} for l in labels}
    for p, g in zip(pred, gt):
        matrix[str(g)][str(p)] = matrix[str(g)].get(str(p), 0) + 1
    return matrix


def summarize_scores(
    predictions: List[int], ground_truth: List[int]
) -> Dict[str, Optional[float]]:
    pred_bin = [collapse_high(p) for p in predictions]
    gt_bin = [collapse_high(g) for g in ground_truth]
    return {
        "n_cases": len(predictions),
        "exact_score_match_rate": exact_match_rate(predictions, ground_truth),
        "mean_absolute_error": mean_absolute_error(predictions, ground_truth),
        "quadratic_weighted_kappa": quadratic_weighted_kappa(predictions, ground_truth),
        "binary_cohen_kappa": cohen_kappa_binary(pred_bin, gt_bin),
        "binary_exact_match_rate": exact_match_rate(pred_bin, gt_bin),
    }
