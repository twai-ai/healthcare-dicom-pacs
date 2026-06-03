"""Dataset registry and manifest loading."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from core.schemas.dataset import DatasetManifestEntry, DatasetRecord
from core.schemas.ground_truth import GroundTruthLabel

REGISTRY_DIR = Path(__file__).resolve().parent
REGISTRY_FILE = REGISTRY_DIR / "datasets.yaml"


def load_registry() -> Dict[str, DatasetRecord]:
    with open(REGISTRY_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    out: Dict[str, DatasetRecord] = {}
    for item in data.get("datasets", []):
        rec = DatasetRecord(**item)
        out[rec.id] = rec
    return out


def get_dataset(dataset_id: str) -> DatasetRecord:
    registry = load_registry()
    if dataset_id not in registry:
        raise KeyError(f"Unknown dataset: {dataset_id}. Available: {list(registry)}")
    return registry[dataset_id]


def load_manifest(
    dataset_id: str, repo_root: Optional[Path] = None
) -> List[DatasetManifestEntry]:
    ds = get_dataset(dataset_id)
    manifest_path = REGISTRY_DIR / ds.manifest
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    entries: List[DatasetManifestEntry] = []
    root = repo_root or Path(__file__).resolve().parents[2]

    with open(manifest_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dicom_path = row["dicom_path"]
            if not Path(dicom_path).is_absolute():
                dicom_path = str(root / dicom_path)
            entries.append(
                DatasetManifestEntry(
                    study_instance_uid=row["study_instance_uid"],
                    patient_id=row["patient_id"],
                    dicom_path=dicom_path,
                    split=row.get("split", "all"),
                    modality=row.get("modality") or None,
                    manufacturer=row.get("manufacturer") or None,
                )
            )
    return entries


def load_ground_truth(dataset_id: str) -> Dict[str, GroundTruthLabel]:
    ds = get_dataset(dataset_id)
    if not ds.ground_truth:
        return {}
    gt_path = REGISTRY_DIR / ds.ground_truth
    if not gt_path.exists():
        return {}

    by_uid: Dict[str, GroundTruthLabel] = {}
    with open(gt_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = GroundTruthLabel(
                study_instance_uid=row["study_instance_uid"],
                patient_id=row.get("patient_id") or None,
                pattern_score_gt=int(row["pattern_score_gt"])
                if row.get("pattern_score_gt")
                else None,
                pattern_label_gt=row.get("pattern_label_gt") or None,
                severity_gt=row.get("severity_gt") or None,
                covid_label=row.get("covid_label") or None,
                reader_id=row.get("reader_id") or None,
                source=row.get("source", "manual"),
            )
            by_uid[label.study_instance_uid] = label
    return by_uid


def compute_dataset_statistics(
    entries: List[DatasetManifestEntry],
    labels: Dict[str, GroundTruthLabel],
) -> Dict:
    from collections import Counter

    existing = [e for e in entries if Path(e.dicom_path).exists()]
    modalities = Counter(e.modality or "unknown" for e in existing)
    splits = Counter(e.split for e in existing)
    manufacturers = Counter(e.manufacturer or "unknown" for e in existing)
    label_dist = Counter(
        labels[e.study_instance_uid].pattern_label_gt
        for e in existing
        if e.study_instance_uid in labels and labels[e.study_instance_uid].pattern_label_gt
    )

    return {
        "manifest_entries": len(entries),
        "files_present": len(existing),
        "files_missing": len(entries) - len(existing),
        "modality_distribution": dict(modalities),
        "split_distribution": dict(splits),
        "manufacturer_distribution": dict(manufacturers),
        "ground_truth_label_distribution": dict(label_dist),
        "patients_unique": len({e.patient_id for e in existing}),
    }
