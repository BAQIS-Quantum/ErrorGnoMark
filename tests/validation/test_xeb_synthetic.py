"""Horizon C — synthetic ground-truth tests for XEB analysis."""

from __future__ import annotations

import pytest

from tests.conftest import require_scipy
from tests.validation.conftest import RB_P_ABS_TOL, RNG, Fidelity_ABS_TOL


def _xeb():
    require_scipy()
    from egm.analysis import xeb as mod

    return mod


def _depolarized_noisy(
    ideal: dict[str, float], epsilon: float, num_qubits: int
) -> dict[str, float]:
    """Mix ideal distribution with uniform: p_exp = (1-eps)*ideal + eps/d."""
    d = 2**num_qubits
    uniform = 1.0 / d
    return {k: (1.0 - epsilon) * ideal.get(k, 0.0) + epsilon * uniform for k in ideal}


def test_s1_analytic_fidelity_single_qubit():
    """S1: hand-checkable non-uniform ideal + depolarizing noise (1 qubit)."""
    num_qubits = 1
    ideal = {"0": 0.7, "1": 0.3}
    epsilon = 0.1
    noisy = _depolarized_noisy(ideal, epsilon, num_qubits)

    d = 2**num_qubits
    exp_dot = sum(ideal[k] * noisy[k] for k in ideal)
    exp_ideal = sum(p**2 for p in ideal.values())
    f_true = (exp_dot - 1 / d) / (exp_ideal - 1 / d)

    xeb = _xeb()
    f_est = xeb.analyze_xeb_fidelity(ideal, noisy, num_qubits)
    assert f_est == pytest.approx(f_true, abs=Fidelity_ABS_TOL)


def test_s1_perfect_distribution_fidelity_near_one():
    """S1b: noisy equals ideal -> normalized fidelity ~ 1."""
    num_qubits = 2
    ideal = {"00": 0.55, "01": 0.15, "10": 0.15, "11": 0.15}
    noisy = dict(ideal)
    xeb = _xeb()
    f_est = xeb.analyze_xeb_fidelity(ideal, noisy, num_qubits)
    assert f_est == pytest.approx(1.0, abs=1e-2)


def test_s2_exponential_fit_recovers_p():
    """S2: depth-resolved mean fidelities follow A*p^m+B; fit recovers p."""
    num_qubits = 2
    A, p_true, B = 0.45, 0.985, 0.05
    depths = [2, 5, 8, 12, 20, 35]
    fidelities = {
        d: [float(A * (p_true**d) + B + RNG.normal(0, 0.002)) for _ in range(8)]
        for d in depths
    }
    xeb = _xeb()
    fit = xeb.fit_xeb_data(fidelities=fidelities, num_qubits=num_qubits, error_bar_mode="sem")
    assert fit["fit_successful"] is True
    assert fit["p"] == pytest.approx(p_true, abs=RB_P_ABS_TOL)


def test_s3_error_bar_nonzero_with_replicates():
    """S3: multiple circuits per depth -> SEM > 0."""
    values = [0.91, 0.93, 0.89, 0.92, 0.90]
    xeb = _xeb()
    err = xeb._compute_error(values, mode="sem")
    assert err > 0.0
    fit = xeb.fit_xeb_data(
        fidelities={5: values, 10: [0.8, 0.82, 0.79], 15: [0.7, 0.72, 0.71]},
        num_qubits=1,
        error_bar_mode="sem",
    )
    assert fit["fit_successful"] is True
    assert all(e >= 0.0 for e in fit["std_errors"])


def test_failure_insufficient_depth_points():
    """Documented failure mode: <3 depths cannot fit."""
    xeb = _xeb()
    fit = xeb.fit_xeb_data(fidelities={1: [0.9], 2: [0.85]}, num_qubits=1)
    assert fit["fit_successful"] is False
