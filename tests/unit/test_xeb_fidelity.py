"""Unit tests for XEB fidelity helper (fast, no executor)."""

from __future__ import annotations

import pytest

from tests.conftest import require_scipy


@pytest.mark.unit
def test_xeb_fidelity_perfect_match():
    require_scipy()
    from egm.analysis.xeb import analyze_xeb_fidelity

    ideal = {"0": 0.7, "1": 0.3}
    noisy = dict(ideal)
    f = analyze_xeb_fidelity(ideal, noisy, num_qubits=1)
    assert f == pytest.approx(1.0, abs=1e-2)


@pytest.mark.unit
def test_xeb_fidelity_empty_returns_zero():
    require_scipy()
    from egm.analysis.xeb import analyze_xeb_fidelity

    assert analyze_xeb_fidelity({}, {"0": 1.0}, num_qubits=1) == 0.0
