# File Path: errorgnomark/backends/flexible_statevector_backend.py
# [FINAL OPTIMIZED VERSION — with analytic depolarizing noise model]
# Compatible with your existing framework and identical API to previous version.

import numpy as np
import random
from typing import Tuple, Dict, Any, Optional
from collections import Counter

# --- Framework Imports ---
try:
    from .base_backend import BaseBackend
    from ..circuits.circuit import QuantumCircuit, Gate
    from ..simulators.statevector_simulator import StatevectorSimulator
except (ImportError, ValueError):
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from egm.core.backends.base_backend import BaseBackend
    from egm.core.circuits.circuit import QuantumCircuit, Gate
    from egm.core.backends.simulators.statevector_simulator import StatevectorSimulator


DEFAULT_SHOTS = 1024
ONE_QUBIT_PAULIS = ['x', 'y', 'z']
TWO_QUBIT_PAULIS = [p1 + p2 for p1 in 'ixyz' for p2 in 'ixyz' if p1 + p2 != 'ii']


class FlexibleStatevectorBackend(BaseBackend):
    """
    Flexible simulator backend that supports both ideal and noisy (depolarizing)
    quantum circuit execution. Uses the StatevectorSimulator underneath.

    - Ideal mode → one fast vector simulation + multinomial sampling.
    - Noisy mode → applies analytic depolarizing channel on final density matrix.
    """

    def __init__(self,
                 depolarizing_error_1q: float = 0.0,
                 depolarizing_error_2q: float = 0.0,
                 **kwargs: Any):
        """
        Args:
            depolarizing_error_1q (float): probability of depolarizing error after each 1q gate.
            depolarizing_error_2q (float): probability of depolarizing error after each 2q gate.
        """
        super().__init__(name="FlexibleStatevectorBackend")

        if not (0.0 <= depolarizing_error_1q < 1.0 and 0.0 <= depolarizing_error_2q < 1.0):
            raise ValueError("Depolarizing error rates must be in [0, 1).")

        self.p1 = depolarizing_error_1q
        self.p2 = depolarizing_error_2q
        self.is_noisy = (self.p1 > 0.0) or (self.p2 > 0.0)

        self._ideal_simulator = StatevectorSimulator()

    # ------------------------------------------------------------------
    def _sample_from_statevector(self, statevector: np.ndarray, num_qubits: int) -> str:
        probabilities = np.abs(statevector) ** 2
        probabilities /= np.sum(probabilities)
        basis_states = [format(i, f'0{num_qubits}b') for i in range(2 ** num_qubits)]
        return np.random.choice(basis_states, p=probabilities)

    # ------------------------------------------------------------------
    def _apply_global_depolarizing(self, rho: np.ndarray, p: float) -> np.ndarray:
        """ Applies depolarizing channel: ρ → (1-p)ρ + p * I/d  """
        if p <= 0.0:
            return rho
        d = rho.shape[0]
        return (1 - p) * rho + p * np.eye(d) / d

    # ------------------------------------------------------------------
    def run(self,
            circuit: QuantumCircuit,
            shots: Optional[int] = None
            ) -> Tuple[Optional[np.ndarray], Dict[str, int]]:
        """
        Executes the given quantum circuit and returns measurement counts.

        Returns
        -------
        statevector : np.ndarray or None
            Final pure state if ideal simulation, else None (mixed-state representation).
        counts : Dict[str, int]
            Counts dictionary of bitstrings → frequency.
        """
        if shots is None:
            shots = DEFAULT_SHOTS

        num_qubits = len(circuit.qubits)

        # === 1️⃣ IDEAL SIMULATION PATH ===========================================
        if not self.is_noisy:
            final_statevector = self._ideal_simulator.run(circuit)
            probabilities = np.abs(final_statevector) ** 2
            probabilities /= np.sum(probabilities)
            counts_array = np.random.multinomial(shots, probabilities)
            counts = {
                format(i, f'0{num_qubits}b'): int(c)
                for i, c in enumerate(counts_array) if c > 0
            }
            return final_statevector, counts

        # === 2️⃣ ANALYTIC NOISY PATH (FAST) =====================================
        # Instead of Monte Carlo per shot, we compute once and apply mean depolarization
        final_statevector = self._ideal_simulator.run(circuit)
        rho = np.outer(final_statevector, final_statevector.conj())

        # Estimate an effective total depolarizing probability
        # (for simplicity, approximate 2q noise dominates if circuit has 2q gates)
        n1 = sum(1 for g in circuit.gates if len(g.qubits) == 1)
        n2 = sum(1 for g in circuit.gates if len(g.qubits) == 2)
        p_eff = 1 - ((1 - self.p1) ** n1 * (1 - self.p2) ** n2)
        if p_eff > 0:
            rho = self._apply_global_depolarizing(rho, p_eff)

        # Measurement probabilities
        probs = np.real(np.diag(rho))
        probs = np.maximum(probs, 0.0)
        probs /= np.sum(probs)

        # Multinomial sampling
        counts_array = np.random.multinomial(shots, probs)
        counts = {
            format(i, f'0{num_qubits}b'): int(c)
            for i, c in enumerate(counts_array) if c > 0
        }
        return None, counts