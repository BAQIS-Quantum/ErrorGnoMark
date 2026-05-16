"""Horizon C — synthetic ground-truth tests for RB analysis."""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import require_scipy
from tests.validation.conftest import RB_EPC_REL_TOL, RB_P_ABS_TOL, RNG


def _rb():
    require_scipy()
    from egm.analysis import rb as mod

    return mod


def _rb_survival(m: float, A: float, p: float, B: float) -> float:
    return float(A * (p**m) + B)


def test_r1_fit_recovers_p_and_epc():
    """R1: synthetic survival curve; fit_rb_data recovers p and EPC."""
    num_qubits = 1
    A, p_true, B = 1 - 1 / 2, 0.995, 1 / 2
    depths = [1, 2, 5, 10, 20, 40, 60]
    means = [_rb_survival(m, A, p_true, B) for m in depths]
    stds = [0.002] * len(depths)

    rb = _rb()
    fit = rb.fit_rb_data(depths=depths, means=means, stds=stds, num_qubits=num_qubits)
    assert fit["fit_successful"] is True
    assert fit["p"] == pytest.approx(p_true, abs=RB_P_ABS_TOL)

    d = 2**num_qubits
    epc_true = ((d - 1) / d) * (1 - p_true)
    assert fit["epc"] == pytest.approx(epc_true, rel=RB_EPC_REL_TOL)


def test_r1_with_shot_noise_replicates():
    """R1b: analyze_rb_standard aggregates replicates and fits."""
    A, p_true, B = 0.48, 0.992, 0.02
    depths = [2, 5, 10, 25, 50]
    results = []
    for m in depths:
        base = _rb_survival(m, A, p_true, B)
        for _ in range(6):
            p_surv = float(np.clip(base + RNG.normal(0, 0.003), 0.0, 1.0))
            results.append(
                {
                    "data": {"0": p_surv},
                    "metadata": {"depth": m},
                }
            )

    rb = _rb()
    out = rb.analyze_rb_standard(results)
    assert out.success is True
    p_fit = next(p.value for p in out.fit.params if p.name == "p")
    assert p_fit == pytest.approx(p_true, abs=RB_P_ABS_TOL)
    assert out.sequence_data
    assert any((pt.std_error or 0.0) > 0.0 for pt in out.sequence_data)


def test_r2_two_qubit_ground_state_key_length():
    """R2: 2-qubit RB uses bitstring keys; EPC formula uses d=4."""
    A, p_true, B = 0.75, 0.99, 0.25
    depths = [2, 4, 8, 16, 32]
    results = []
    for m in depths:
        base = _rb_survival(m, A, p_true, B)
        for _ in range(5):
            surv = float(np.clip(base + RNG.normal(0, 0.004), 0.0, 1.0))
            results.append({"data": {"00": surv}, "metadata": {"depth": m}})

    rb = _rb()
    out = rb.analyze_rb_standard(results)
    assert out.success is True
    p_fit = next(p.value for p in out.fit.params if p.name == "p")
    assert p_fit == pytest.approx(p_true, abs=0.03)


def test_failure_insufficient_rb_points():
    rb = _rb()
    fit = rb.fit_rb_data(depths=[1, 2], means=[0.9, 0.85], stds=[0.01, 0.01], num_qubits=1)
    assert fit["fit_successful"] is False
