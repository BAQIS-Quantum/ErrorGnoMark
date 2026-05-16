"""Unit tests for RB EPC formula and fit boundaries."""

from __future__ import annotations

import pytest

from tests.conftest import require_scipy


@pytest.mark.unit
def test_rb_fit_recovers_known_p():
    require_scipy()
    from egm.analysis.rb import fit_rb_data

    depths = [1, 2, 5, 10, 20, 40]
    p_true = 0.994
    A, B = 0.5, 0.5
    means = [A * (p_true**m) + B for m in depths]
    fit = fit_rb_data(depths=depths, means=means, stds=[0.001] * len(depths), num_qubits=1)
    assert fit["fit_successful"] is True
    assert fit["p"] == pytest.approx(p_true, abs=0.02)


@pytest.mark.unit
def test_rb_fit_fails_with_two_points():
    require_scipy()
    from egm.analysis.rb import fit_rb_data

    fit = fit_rb_data(depths=[1, 2], means=[0.9, 0.85], stds=[0.01, 0.01], num_qubits=1)
    assert fit["fit_successful"] is False
