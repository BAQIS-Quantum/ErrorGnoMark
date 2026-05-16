"""Root pytest configuration for ErrorGnoMark."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure `src` layout is importable without editable install in minimal envs.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def require_scipy() -> None:
    """Skip test when SciPy cannot import (broken local envs); CI installs scipy~=1.13."""
    try:
        import scipy.optimize  # noqa: F401
    except Exception as exc:
        pytest.skip(f"scipy unavailable: {exc}")
