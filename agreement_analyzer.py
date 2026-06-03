#!/usr/bin/env python3
"""Standalone agreement analysis from a completed evaluation run directory."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from core.evaluation.agreement_analyzer import compare_engine_to_ground_truth
from core.registry.loader import load_ground_truth
from core.schemas.findings import StructuredFindings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path, help="evaluations/run_* directory")
    parser.add_argument("--dataset", default="covid19_tcia_showcase")
    args = parser.parse_args()

    preds = []
    for line in (args.run_dir / "predictions.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            preds.append(StructuredFindings.model_validate(json.loads(line)))

    labels = load_ground_truth(args.dataset)
    result = compare_engine_to_ground_truth(preds, labels)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
