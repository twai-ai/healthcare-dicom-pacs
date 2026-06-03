#!/usr/bin/env python3
"""Import ground truth CSV into PostgreSQL (optional; file-based eval works without DB)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from core.registry.loader import get_dataset, load_ground_truth


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ds = get_dataset(args.dataset)
    labels = load_ground_truth(args.dataset)
    print(f"Dataset: {ds.name} v{ds.version}")
    print(f"Labels loaded: {len(labels)}")
    for uid, label in labels.items():
        print(f"  {uid}: score_gt={label.pattern_score_gt} label={label.pattern_label_gt}")
    if args.dry_run:
        print("(dry run — DB import requires webapp database session)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
