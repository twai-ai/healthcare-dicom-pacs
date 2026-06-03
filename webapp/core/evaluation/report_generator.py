"""Generate reproducible evaluation reports (Markdown + JSON)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def generate_markdown_report(
    run_config: Dict[str, Any],
    dataset_stats: Dict[str, Any],
    agreement: Dict[str, Any],
    engine_metrics: Dict[str, Any],
) -> str:
    lines = [
        "# DICOM-AI Evaluation Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Run ID:** {run_config.get('run_id', 'unknown')}",
        f"**Dataset:** {run_config.get('dataset_id')} v{run_config.get('dataset_version', '?')}",
        f"**Engine:** {run_config.get('engine_version')}",
        "",
        "> Automated imaging observations for research evaluation. Not a clinical diagnosis.",
        "",
        "## Dataset statistics",
        "",
        f"- Manifest entries: {dataset_stats.get('manifest_entries', 0)}",
        f"- DICOM files present: {dataset_stats.get('files_present', 0)}",
        f"- Missing files: {dataset_stats.get('files_missing', 0)}",
        f"- Unique patients: {dataset_stats.get('patients_unique', 0)}",
        "",
        "### Modality distribution",
        "",
        "```json",
        json.dumps(dataset_stats.get("modality_distribution", {}), indent=2),
        "```",
        "",
        "## Engine vs ground truth",
        "",
    ]

    em = engine_metrics.get("metrics", {})
    lines.extend(
        [
            f"- Cases evaluated: {em.get('n_cases', 0)}",
            f"- Exact score match: **{em.get('exact_score_match_rate', 0) * 100:.1f}%**"
            if em.get("exact_score_match_rate") is not None
            else "- Exact score match: N/A",
            f"- Mean absolute error: {em.get('mean_absolute_error', 'N/A')}",
            f"- Quadratic weighted κ: {em.get('quadratic_weighted_kappa', 'N/A')}",
            "",
        ]
    )

    lines.append("## AI agreement (parsed from stored or optional API outputs)")
    lines.append("")
    for ai in agreement.get("ai_vs_ground_truth", []):
        name = ai.get("comparison", "model").replace("_vs_ground_truth", "")
        lines.append(
            f"- **{name.title()} agreement:** {ai.get('agreement_display', 'N/A')} "
            f"(n={ai.get('n_paired', 0)})"
        )

    lines.extend(
        [
            "",
            "## Reproducibility",
            "",
            "Re-run with:",
            "",
            "```bash",
            f"python -m core.evaluation.benchmark_runner --dataset {run_config.get('dataset_id')}",
            "```",
            "",
            f"Git commit: `{run_config.get('git_commit', 'unknown')}`",
            "",
        ]
    )

    return "\n".join(lines)


def write_report_bundle(
    output_dir: Path,
    run_config: Dict[str, Any],
    dataset_stats: Dict[str, Any],
    predictions: list,
    agreement: Dict[str, Any],
    engine_metrics: Dict[str, Any],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "config.json").write_text(
        json.dumps(run_config, indent=2), encoding="utf-8"
    )
    (output_dir / "dataset_statistics.json").write_text(
        json.dumps(dataset_stats, indent=2), encoding="utf-8"
    )
    (output_dir / "predictions.jsonl").write_text(
        "\n".join(json.dumps(p) for p in predictions) + ("\n" if predictions else ""),
        encoding="utf-8",
    )
    (output_dir / "agreement.json").write_text(
        json.dumps(agreement, indent=2), encoding="utf-8"
    )
    (output_dir / "metrics.json").write_text(
        json.dumps(engine_metrics, indent=2), encoding="utf-8"
    )

    md = generate_markdown_report(
        run_config, dataset_stats, agreement, engine_metrics
    )
    report_path = output_dir / "evaluation_report.md"
    report_path.write_text(md, encoding="utf-8")
    return report_path
