"""Resolve repo root so `core` imports work locally and in Docker."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List


def repo_root_candidates() -> List[Path]:
    here = Path(__file__).resolve().parent
    return [
        Path("/workspace"),
        here.parent.parent,
        *here.parents,
    ]


def ensure_repo_on_sys_path() -> Path:
    for root in repo_root_candidates():
        if root.is_dir() and (root / "core" / "diagnostic_engine.py").is_file():
            s = str(root)
            if s not in sys.path:
                sys.path.insert(0, s)
            return root
    raise ImportError(
        "Cannot find core/diagnostic_engine.py. "
        "Local dev: run from repo checkout. Docker: mount repo at /workspace."
    )
