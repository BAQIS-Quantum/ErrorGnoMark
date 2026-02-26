# File Path: errorgnomark/src/egm/core/experiments/benchmarking/tools/rb_tools.py
"""
RB helper utilities shared by 1Q/2Q Randomized Benchmarking code.

This module intentionally keeps only *small*, dependency-light helpers:
- Measurement detection & "ensure measure_all" fallback
- Circuit remapping without measurement for 1Q/2Q templates
- Local survival probability (marginalization) for 1Q and 2Q from raw counts
- Small list utilities (dedup + pair normalization)

NOTE: All functions are kept with leading underscores to emphasize they are
internal helpers. They are exported via __all__ for explicit, stable imports
from other packages within this project.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Mapping

from egm.core.circuits.circuit import QuantumCircuit, Gate

__all__ = [
    # Measurement helpers
    "_is_measure_gate",
    "_ensure_measure_all_if_missing",
    # 1Q helpers
    "_remap_1q_circuit_no_meas",
    "_rb_local_survival_1q_from_counts",
    # 2Q helpers
    "_remap_2q_circuit_no_meas",
    "_rb_local_survival_2q_from_counts",
    # Small utilities
    "_dedup_keep_order",
    "_normalize_pairs",
    "_clone_gate_with_params",
]


# ---------------------------------------------------------------------------
# Measurement helpers
# ---------------------------------------------------------------------------

def _is_measure_gate(g: Any) -> bool:
    """Return True if ``g`` is a measurement/readout gate."""
    name = getattr(g, "name", "").lower()
    if getattr(g, "is_measure", False):
        return True
    return name in ("measure", "m", "meas", "mz", "readout")


def _ensure_measure_all_if_missing(qc: QuantumCircuit) -> None:
    """Ensure a circuit has at least one measurement; add ``measure_all()`` if missing."""
    has_meas = any(_is_measure_gate(g) for g in getattr(qc, "gates", []))
    if not has_meas:
        qc.measure_all()


# ---------------------------------------------------------------------------
# 1Q helpers
# ---------------------------------------------------------------------------

def _remap_1q_circuit_no_meas(qc: QuantumCircuit, dst_q: int) -> QuantumCircuit:
    """
    Remap a *single-qubit* template ``qc`` onto ``dst_q`` while skipping any
    measurement gates. The returned circuit contains only 1Q gates on ``dst_q``.
    """
    new_gates: List[Gate] = []
    for g in getattr(qc, "gates", []):
        if _is_measure_gate(g):
            continue
        if hasattr(g, "qubits") and len(g.qubits) == 1:
            new_gates.append(Gate(g.name, (dst_q,)))
    return QuantumCircuit(qubits=[dst_q], gates=new_gates)


def _rb_local_survival_1q_from_counts(
    noisy_counts: Mapping[str, int],
    qubit_order: List[int],
    qubit: int,
) -> float:
    """
    Marginalize multi-qubit measurement counts onto a single target ``qubit`` and
    compute the probability of measuring |0> on that qubit.

    Assumptions
    ----------
    - Bitstrings in ``noisy_counts`` are aligned to ``qubit_order`` (left-to-right).
    """
    total = sum(noisy_counts.values())
    if total == 0:
        return 0.0
    pos = {q: i for i, q in enumerate(qubit_order)}
    j = pos[qubit]
    survive = sum(c for x, c in noisy_counts.items() if len(x) > j and x[j] == '0')
    return survive / total


# ---------------------------------------------------------------------------
# 2Q helpers
# ---------------------------------------------------------------------------

def _remap_2q_circuit_no_meas(
    qc: QuantumCircuit,
    src_pair: Tuple[int, int],
    dst_pair: Tuple[int, int],
) -> QuantumCircuit:
    """
    Remap gates that act on ``src_pair`` to the corresponding ``dst_pair`` while
    skipping measurement gates.

    - 1Q gates on either source qubit are mapped to the matching destination qubit.
    - 2Q gates are kept only if *all* participating qubits map into ``dst_pair``.
    """
    s0, s1 = src_pair
    d0, d1 = dst_pair
    mapping = {s0: d0, s1: d1}

    new_gates: List[Gate] = []
    for g in getattr(qc, "gates", []):
        if _is_measure_gate(g):
            continue
        if not hasattr(g, "qubits"):
            continue
        new_qubits = tuple(mapping.get(q, q) for q in g.qubits)
        if all(q in dst_pair for q in new_qubits):
            new_gates.append(Gate(g.name, new_qubits))

    return QuantumCircuit(qubits=list(dst_pair), gates=new_gates)


def _rb_local_survival_2q_from_counts(
    noisy_counts: Mapping[str, int],
    qubit_order: List[int],
    pair: Tuple[int, int],
) -> float:
    """
    Marginalize multi-qubit measurement counts onto a two-qubit ``pair`` and
    compute the probability of measuring |00> on that pair.

    Assumptions
    ----------
    - Bitstrings in ``noisy_counts`` are aligned to ``qubit_order`` (left-to-right).
    """
    total = sum(noisy_counts.values())
    if total == 0:
        return 0.0
    pos = {q: i for i, q in enumerate(qubit_order)}
    i0, i1 = pos[pair[0]], pos[pair[1]]
    survive = sum(
        c for x, c in noisy_counts.items()
        if len(x) > max(i0, i1) and x[i0] == '0' and x[i1] == '0'
    )
    return survive / total


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

def _dedup_keep_order(seq: List[int]) -> List[int]:
    """De-duplicate a list while preserving the original order."""
    seen: set[int] = set()
    out: List[int] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _normalize_pairs(pairs: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Normalize pairs to sorted tuples: ``(min(q0,q1), max(q0,q1))``."""
    return [tuple(sorted(p)) for p in pairs]


def _clone_gate_with_params(g: Gate, new_qubits: Tuple[int, ...]) -> Gate:
    """Clone a gate while preserving its params (for parameterized gates like U3)."""
    params = getattr(g, "params", None)
    # Handle cases where params might be None, a tuple, or a list
    if params is None:
        return Gate(name=g.name, qubits=tuple(new_qubits))
    # Standardize as tuple to ensure immutability downstream
    return Gate(name=g.name, qubits=tuple(new_qubits), params=tuple(params))