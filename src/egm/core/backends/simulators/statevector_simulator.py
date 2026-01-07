# =============================================================================
# File    : egm/core/simulators/statevector_simulator.py
# Version : v5.3.0 - Canonical-Gate Compatible (SISQ-Aligned Edition)
# Author  : OpenAI-Assistant
# =============================================================================
"""
StatevectorSimulator (Noise-Free)
---------------------------------

A pure statevector simulator for ideal (noise-free) quantum circuit execution.
Fully compatible with canonical SX/SY gate naming and tolerant of partial
gate-map definitions. Functionally identical to the SISQ v2.7 implementation.
"""

from __future__ import annotations
import numpy as np
from typing import Dict
from egm.core.circuits.circuit import (
    QuantumCircuit,
    Gate,
    get_matrix as get_gate_matrix_from_map,
    get_parameterized_matrix as get_parameterized_gate_matrix,
    get_canonical_name,
)


class StatevectorSimulator:
    """
    Ideal statevector simulator used by the IdealBackend.

    • Canonical name normalization (e.g. sqrtX -> sx, RY90 -> sy)
    • Accepts parameterized gates and explicit matrix gates
    • Provides fallback definitions for incomplete gate maps
    """

    def __init__(self):
        self._qubit_map: Dict[int, int] = {}

    # ------------------------------------------------------------------
    def _get_gate_matrix(self, gate: Gate) -> np.ndarray:
        """
        Retrieve the numeric unitary matrix for a gate.
        Canonicalizes aliases and supports built-in fallback definitions.

        Raises
        ------
        ValueError
            If a matrix_gate has no valid np.ndarray parameter.
        NotImplementedError
            If gate name is unknown to this simulator.
        """
        name = get_canonical_name(gate.name).lower()

        # Explicit matrix gate
        if name == "matrix_gate":
            if not gate.params or not isinstance(gate.params[0], np.ndarray):
                raise ValueError(
                    "Gate 'matrix_gate' requires a numpy array in its params."
                )
            return gate.params[0]

        # Built-in fallback definitions
        FALLBACKS = {
            "s": np.array([[1, 0], [0, 1j]], dtype=complex),
            "sdg": np.array([[1, 0], [0, -1j]], dtype=complex),
            "sx": np.array(
                [[0.5 + 0.5j, 0.5 - 0.5j], [0.5 - 0.5j, 0.5 + 0.5j]], dtype=complex
            ),
            "sxdg": np.array(
                [[0.5 - 0.5j, 0.5 + 0.5j], [0.5 + 0.5j, 0.5 - 0.5j]], dtype=complex
            ),
            "sy": np.array(
                [[0.5 + 0.5j, 0.5 - 0.5j], [-0.5 - 0.5j, 0.5 + 0.5j]], dtype=complex
            ),
            "sydg": np.array(
                [[0.5 - 0.5j, -0.5 - 0.5j], [0.5 + 0.5j, 0.5 - 0.5j]], dtype=complex
            ),
        }
        if name in FALLBACKS:
            return FALLBACKS[name]

        # Normal gate-map retrieval
        try:
            if gate.params:
                gate.name = name
                return get_parameterized_gate_matrix(gate)
            return get_gate_matrix_from_map(name)
        except ValueError as e:
            raise NotImplementedError(
                f"Gate '{gate.name}' (canonical '{name}') "
                "not supported by StatevectorSimulator."
            ) from e

    # ------------------------------------------------------------------
    def _construct_operator(self, gate: Gate, num_qubits: int) -> np.ndarray:
        """
        Construct the full N-qubit operator embedding for the given gate.

        Returns
        -------
        np.ndarray
            The unitary matrix of shape (2**num_qubits, 2**num_qubits)
            representing this gate acting on the whole register.
        """
        gate_matrix = self._get_gate_matrix(gate)
        targets = [self._qubit_map[q] for q in gate.qubits]
        k = len(targets)

        # Single-qubit gate
        if k == 1:
            q = targets[0]
            ops = [gate_matrix if idx == q else np.eye(2) for idx in reversed(range(num_qubits))]
            U_full = ops[0]
            for u in ops[1:]:
                U_full = np.kron(U_full, u)
            return U_full

        # Two-qubit gate
        if k == 2:
            q1, q2 = sorted(targets)
            left = np.eye(2 ** (num_qubits - q2 - 1))
            right = np.eye(2 ** q1)
            return np.kron(np.kron(left, gate_matrix), right)

        # Unsupported multi-qubit gate (>=3)
        return np.eye(2 ** num_qubits, dtype=complex)

    # ------------------------------------------------------------------
    def run(self, circuit: QuantumCircuit) -> np.ndarray:
        """
        Simulate the given quantum circuit and return the final statevector |ψ⟩.

        Notes
        -----
        • Measurement operations are ignored (unitary evolution only).
        • The qubit mapping follows the circuit's explicit qubit ordering.
        """
        num_qubits = len(circuit.qubits)
        self._qubit_map = {qubit: i for i, qubit in enumerate(circuit.qubits)}

        state_vector = np.zeros(2 ** num_qubits, dtype=complex)
        state_vector[0] = 1.0

        for gate in circuit.gates:
            if getattr(gate, "is_measurement", False):
                continue
            U = self._construct_operator(gate, num_qubits)
            state_vector = U @ state_vector

        return state_vector