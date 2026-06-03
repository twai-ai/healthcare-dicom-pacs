"""Quantitative feature extraction from DICOM pixel data."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pydicom
from scipy import stats


def extract_quantitative_features(ds: pydicom.Dataset) -> Dict[str, Any]:
    if not hasattr(ds, "pixel_array"):
        return {}

    img = ds.pixel_array.astype(float)
    is_hu = False

    if hasattr(ds, "RescaleIntercept") and hasattr(ds, "RescaleSlope"):
        img = img * float(ds.RescaleSlope) + float(ds.RescaleIntercept)
        is_hu = ds.Modality == "CT"

    features: Dict[str, Any] = {
        "mean_intensity": float(np.mean(img)),
        "median_intensity": float(np.median(img)),
        "std_intensity": float(np.std(img)),
        "min_intensity": float(np.min(img)),
        "max_intensity": float(np.max(img)),
        "intensity_range": float(np.max(img) - np.min(img)),
        "coefficient_of_variation": float(np.std(img) / np.mean(img))
        if np.mean(img) > 0
        else 0.0,
        "p25": float(np.percentile(img, 25)),
        "p75": float(np.percentile(img, 75)),
        "p95": float(np.percentile(img, 95)),
        "p05": float(np.percentile(img, 5)),
        "histogram_skewness": float(_safe_skew(img)),
        "histogram_kurtosis": float(_safe_kurtosis(img)),
        "image_entropy": float(_image_entropy(img)),
        "is_hounsfield": is_hu,
    }

    if is_hu:
        features.update(_analyze_ct_densities(img))
    else:
        features.update(_analyze_xray_patterns(img))

    return features


def _safe_skew(img: np.ndarray) -> float:
    try:
        return float(stats.skew(img.flatten()))
    except Exception:
        return 0.0


def _safe_kurtosis(img: np.ndarray) -> float:
    try:
        return float(stats.kurtosis(img.flatten()))
    except Exception:
        return 0.0


def _image_entropy(img: np.ndarray) -> float:
    from scipy.stats import entropy as scipy_entropy

    try:
        hist, _ = np.histogram(img.flatten(), bins=256)
        hist = hist / hist.sum()
        return float(scipy_entropy(hist + 1e-10))
    except Exception:
        return 0.0


def _analyze_ct_densities(img_hu: np.ndarray) -> Dict[str, Any]:
    analysis = {
        "air_proportion": float(np.sum(img_hu < -500) / img_hu.size),
        "soft_tissue_proportion": float(
            np.sum((img_hu >= -100) & (img_hu <= 100)) / img_hu.size
        ),
        "bone_proportion": float(np.sum(img_hu > 300) / img_hu.size),
        "ground_glass_pattern": False,
        "consolidation_pattern": False,
    }
    gg_range = np.sum((img_hu >= -700) & (img_hu <= -300))
    if gg_range / img_hu.size > 0.1:
        analysis["ground_glass_pattern"] = True
    consolidation = np.sum((img_hu >= -100) & (img_hu <= 100))
    if consolidation / img_hu.size > 0.05:
        analysis["consolidation_pattern"] = True
    return analysis


def _analyze_xray_patterns(img: np.ndarray) -> Dict[str, Any]:
    height, width = img.shape
    upper_third = img[: height // 3, :]
    middle_third = img[height // 3 : 2 * height // 3, :]
    lower_third = img[2 * height // 3 :, :]
    left_mean = float(np.mean(img[:, : width // 2]))
    right_mean = float(np.mean(img[:, width // 2 :]))
    mean_img = float(np.mean(img))

    analysis: Dict[str, Any] = {
        "upper_mean": float(np.mean(upper_third)),
        "middle_mean": float(np.mean(middle_third)),
        "lower_mean": float(np.mean(lower_third)),
        "left_half_mean": left_mean,
        "right_half_mean": right_mean,
        "bilateral_asymmetry": float(abs(left_mean - right_mean) / mean_img)
        if mean_img > 0
        else 0.0,
        "peripheral_mean": float(_peripheral_mean(img)),
        "central_mean": float(_central_mean(img)),
    }

    lower_std = float(np.std(lower_third))
    analysis["lower_field_heterogeneity"] = lower_std > float(np.std(img)) * 1.2
    return analysis


def _peripheral_mean(img: np.ndarray) -> float:
    h, w = img.shape
    border = min(h, w) // 10
    peripheral = np.concatenate(
        [
            img[:border, :].flatten(),
            img[-border:, :].flatten(),
            img[:, :border].flatten(),
            img[:, -border:].flatten(),
        ]
    )
    return float(np.mean(peripheral))


def _central_mean(img: np.ndarray) -> float:
    h, w = img.shape
    return float(np.mean(img[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]))
