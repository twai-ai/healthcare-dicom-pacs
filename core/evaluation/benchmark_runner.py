#!/usr/bin/env python3
"""
Reproducible benchmark runner for DICOM-AI evaluation framework.

Usage:
  python -m core.evaluation.benchmark_runner --dataset covid19_tcia_showcase
  python -m core.evaluation.benchmark_runner --dataset covid19_tcia_showcase --include-ai
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.diagnostic_engine import DiagnosticEngine, ENGINE_VERSION
from core.dicom_io import read_dicom, metadata_from_dataset
from core.evaluation.agreement_analyzer import (
    compare_engine_to_ground_truth,
    compare_labels_to_ground_truth,
    full_agreement_report,
)
from core.evaluation.ai_label_parser import parse_ai_analysis
from core.evaluation.report_generator import write_report_bundle
from core.registry.loader import (
    compute_dataset_statistics,
    get_dataset,
    load_ground_truth,
    load_manifest,
)


def _git_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except Exception:
        return "unknown"


def _load_ai_json_outputs(output_dir: Path) -> Dict[str, Dict[str, str]]:
    """Load optional AI text from test-code/output JSON if present."""
    by_patient: Dict[str, Dict[str, str]] = {}
    multimodel = output_dir / "multimodel_analysis_results.json"
    if multimodel.exists():
        try:
            data = json.loads(multimodel.read_text(encoding="utf-8"))
            for item in data if isinstance(data, list) else data.get("results", []):
                pid = item.get("patient_id") or item.get("metadata", {}).get("patient_id")
                if not pid:
                    continue
                by_patient.setdefault(pid, {})
                if item.get("gemini_analysis"):
                    by_patient[pid]["gemini"] = item["gemini_analysis"]
                if item.get("groq_analysis"):
                    by_patient[pid]["groq"] = item["groq_analysis"]
        except Exception:
            pass
    return by_patient


def run_benchmark(
    dataset_id: str,
    output_dir: Optional[Path] = None,
    split: Optional[str] = None,
    include_ai: bool = False,
) -> Path:
    ds_record = get_dataset(dataset_id)
    entries = load_manifest(dataset_id, REPO_ROOT)
    if split:
        entries = [e for e in entries if e.split == split]

    labels = load_ground_truth(dataset_id)
    stats = compute_dataset_statistics(entries, labels)

    engine = DiagnosticEngine()
    findings_list = []
    predictions: List[Dict[str, Any]] = []
    study_uids: List[str] = []

    for entry in entries:
        path = Path(entry.dicom_path)
        if not path.exists():
            continue
        ds = read_dicom(path)
        meta = metadata_from_dataset(ds)
        if not meta.get("study_instance_uid"):
            meta["study_instance_uid"] = entry.study_instance_uid
        findings = engine.analyze(ds, meta)
        findings_list.append(findings)
        study_uids.append(findings.study_instance_uid)
        predictions.append(findings.model_dump(mode="json"))

    engine_vs_gt = compare_engine_to_ground_truth(findings_list, labels)

    ai_comparisons: List[Dict[str, Any]] = []
    if include_ai:
        ai_outputs = _load_ai_json_outputs(REPO_ROOT / "test-code" / "output")
        for model_key, display in [("gemini", "gemini"), ("groq", "groq")]:
            parsed_list = []
            paired_uids = []
            for f in findings_list:
                texts = ai_outputs.get(f.patient_id, {})
                text = texts.get(model_key, "")
                if not text:
                    continue
                parsed_list.append(parse_ai_analysis(text, display))
                paired_uids.append(f.study_instance_uid)
            if parsed_list:
                ai_comparisons.append(
                    compare_labels_to_ground_truth(
                        parsed_list, labels, paired_uids, display
                    )
                )

    agreement = full_agreement_report(engine_vs_gt, ai_comparisons)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = output_dir or (REPO_ROOT / "evaluations" / f"run_{run_id}")

    run_config = {
        "run_id": run_id,
        "dataset_id": dataset_id,
        "dataset_version": ds_record.version,
        "engine_version": ENGINE_VERSION,
        "git_commit": _git_commit(),
        "split": split or "all",
        "include_ai": include_ai,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    report_path = write_report_bundle(
        out,
        run_config,
        stats,
        predictions,
        agreement,
        engine_vs_gt,
    )

    _print_summary(ds_record.name, stats, engine_vs_gt, ai_comparisons, out)
    return report_path


def _print_summary(
    dataset_name: str,
    stats: Dict,
    engine_vs_gt: Dict,
    ai_comparisons: List[Dict],
    out: Path,
) -> None:
    em = engine_vs_gt.get("metrics", {})
    n = em.get("n_cases", 0)
    print("\n" + "=" * 60)
    print("DICOM-AI BENCHMARK COMPLETE")
    print("=" * 60)
    print(f"\nDataset: {dataset_name}")
    print(f"Cases evaluated (with GT): {n}")
    print(f"Files present: {stats.get('files_present', 0)} / {stats.get('manifest_entries', 0)}")
    if em.get("exact_score_match_rate") is not None:
        print(f"\nEngine vs Ground Truth agreement: {em['exact_score_match_rate'] * 100:.1f}%")
        print(f"Mean absolute error: {em.get('mean_absolute_error', 'N/A')}")
    for ai in ai_comparisons:
        name = ai.get("comparison", "").replace("_vs_ground_truth", "").title()
        print(f"{name} agreement: {ai.get('agreement_display', 'N/A')}")
    print(f"\nReproducibility report: {out / 'evaluation_report.md'}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run reproducible DICOM-AI evaluation benchmark"
    )
    parser.add_argument(
        "--dataset",
        default="covid19_tcia_showcase",
        help="Dataset registry ID",
    )
    parser.add_argument("--split", default=None, help="Filter manifest split")
    parser.add_argument("--output", type=Path, default=None, help="Output directory")
    parser.add_argument(
        "--include-ai",
        action="store_true",
        help="Include agreement vs cached AI outputs in test-code/output",
    )
    args = parser.parse_args()

    report = run_benchmark(
        args.dataset,
        output_dir=args.output,
        split=args.split,
        include_ai=args.include_ai,
    )
    print(f"Report written to: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
