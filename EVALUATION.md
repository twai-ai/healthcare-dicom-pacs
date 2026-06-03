# DICOM-AI Evaluation Framework

**ATRISI healthcare ecosystem — scientific rigor over platform breadth.**

This layer answers: *Can DICOM processing, vision AI, heuristic analysis, and technical QA produce useful, explainable, and repeatable observations from imaging datasets?*

## Principles

- **Observations, not diagnoses** — structured JSON findings with disclaimers
- **One engine** — `core.diagnostic_engine.DiagnosticEngine` (v1.0.0) for all code paths
- **Reproducible runs** — versioned datasets, manifests, ground truth, evaluation reports

## Quick start

```bash
# Install evaluation dependencies (repo root)
pip install -r requirements-evaluation.txt

# Rebuild manifest after adding DICOM under data/
python -m core.registry.build_manifest

# Run benchmark
python benchmark_runner.py --dataset covid19_tcia_showcase

# With cached AI outputs from test-code/output (optional)
python benchmark_runner.py --dataset covid19_tcia_showcase --include-ai
```

Outputs: `evaluations/run_YYYYMMDD_HHMMSS/`

- `config.json` — run metadata + git commit
- `predictions.jsonl` — structured findings per study
- `metrics.json` — engine vs ground truth
- `agreement.json` — AI agreement if `--include-ai`
- `evaluation_report.md` — publication-oriented summary

## Dataset registry

- Registry: `core/registry/datasets.yaml`
- Manifest: `core/registry/manifests/*.csv`
- Ground truth: `core/registry/ground_truth/*.csv`

Update ground truth with expert labels; do not treat placeholder consensus labels as clinical truth.

## Scale target

Expand manifest from 2 → 50–100 cases via TCIA ingest (`test-code/06_enhanced_tcia_download.py`) then:

```bash
python -m core.registry.build_manifest
python benchmark_runner.py
```

## Non-goals (this sprint)

RAG, knowledge graphs, copilots, fine-tuning, SaaS monetization.

## Ecosystem note

DICOM-AI evaluation is the **foundation layer** for ATRISI. Future JoaLLM / Knowledge Hub features should consume structured `findings_json`, not replace this pipeline.
