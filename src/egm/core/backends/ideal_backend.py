# =============================================================================
# File    : egm/core/backends/ideal_backend.py
# Version : v5.3.0 - Noise-Free Backend (SISQ-Aligned Edition)
# Author  : OpenAI-Assistant
# =============================================================================
"""
IdealBackend
------------
A perfect, noise-free backend wrapping the StatevectorSimulator.

This implementation is fully aligned with the SISQ (errorgnomark) v1.1 backend
in both behavior and API, while maintaining the EGM package structure.

Features
--------
• Deterministic statevector simulation (no noise)
• Backward-compatibility methods: get_statevector() and statevector_to_probs()
• Fully compatible with all EGM analysis, engine, and benchmarking modules
"""

from __future__ import annotations
from typing import Tuple, Optional, Dict
import numpy as np

from egm.core.backends.base_backend import BaseBackend
from egm.core.circuits.circuit import QuantumCircuit
from egm.core.backends.simulators.statevector_simulator import StatevectorSimulator


# ---------------------------------------------------------------------------
# Noise-Free Backend Implementation
# ---------------------------------------------------------------------------
class IdealBackend(BaseBackend):
    """A perfect, noise-free backend that leverages the StatevectorSimulator."""

    def __init__(self):
        super().__init__(name="IdealBackend")
        self._simulator = StatevectorSimulator()

    # ------------------------------------------------------------------
    def run(
        self,
        circuit: QuantumCircuit,
        shots: Optional[int] = None,
    ) -> Tuple[np.ndarray, None]:
        """
        Execute the input circuit using a deterministic statevector simulator.

        Parameters
        ----------
        circuit : QuantumCircuit
            Circuit object to simulate.
        shots : Optional[int]
            Ignored (retained for interface compatibility).

        Returns
        -------
        Tuple[np.ndarray, None]
            (statevector, None) pair, where the second element is a placeholder
            for count data in noise-free mode.
        """
        statevector = self._simulator.run(circuit)
        return statevector, None

    # ------------------------------------------------------------------
    # Backward-Compatibility Utilities
    # ------------------------------------------------------------------
    def get_statevector(self, circuit: QuantumCircuit) -> np.ndarray:
        """
        Return the ideal statevector for the given circuit.

        This method is provided to maintain compatibility with legacy
        benchmarking workflows that expected IdealBackend to expose
        a `get_statevector()` interface.
        """
        statevector, _ = self.run(circuit)
        return statevector

    def statevector_to_probs(self, statevector: np.ndarray) -> Dict[str, float]:
        """
        Convert a statevector to a probability dictionary mapping bitstrings
        to their respective probabilities.

        Parameters
        ----------
        statevector : np.ndarray
            Complex statevector of dimension 2**n.

        Returns
        -------
        Dict[str, float]
            {bitstring: probability} for all non-negligible outcomes.
        """
        num_qubits = int(np.log2(len(statevector)))
        probs = np.abs(statevector) ** 2
        return {
            format(i, f"0{num_qubits}b"): float(p)
            for i, p in enumerate(probs)
            if p > 1e-12
        }