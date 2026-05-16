"""Shared tolerances and seeds for Horizon C synthetic validation tests."""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import require_scipy


@pytest.fixture(autouse=True)
def _ensure_scipy() -> None:
    require_scipy()

# Athena-approved defaults for v1 validation program (2026-05-16).
RNG = np.random.default_rng(42)

Fidelity_ABS_TOL = 1e-3
RB_P_ABS_TOL = 0.02
RB_EPC_REL_TOL = 0.05

pytestmark = pytest.mark.validation
