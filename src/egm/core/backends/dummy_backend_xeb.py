# =============================================================================
# File    : egm/core/backends/dummy_backend_xeb.py
# Version : v5.3.0 - UnifiedMatrixBackend (SISQ-Aligned Edition)
# Author  : OpenAI-Assistant
# =============================================================================
"""
UnifiedMatrixBackend - Dummy Backend for XEB/SPB Simulation
-----------------------------------------------------------

Fully aligned with SISQ (errorgnomark) v4.5.0 backend.

Purpose
-------
• Provides a realistic but maintainable matrix-based noise model
  for Interleaved-XEB and SPB simulations.
• Uses canonical gate matrices directly from circuit definitions.
• Adds extra decoherence for 2-qubit entangling gates (e.g., CZ, CNOT)
  to ensure p_int < p_ref fidelity behavior.

Behavior
--------
- Matrix-based pure-state propagation for ideal probabilities.
- Mild depolarization, T1/T2 bias, coherent drift, and sampling noise.
"""

from __future__ import annotations
import numpy as np
from typing import List, Dict, Optional, Tuple

from egm.core.circuits.circuit import (
    QuantumCircuit,
    Gate,
    get_canonical_name,
    get_matrix as get_gate_matrix_from_map,
    get_parameterized_matrix as get_parameterized_gate_matrix,
)
from egm.core.backends.base_backend import BaseBackend


# -----------------------------------------------------------------------------
# Helper: unified access to canonical gate matrices
# -----------------------------------------------------------------------------
def _gate_matrix(name: str, params: Optional[List[float]] = None) -> np.ndarray:
    """Return a canonical gate matrix, parameterized if applicable."""
    canonical_name = get_canonical_name(name)
    if params:
        g = Gate(canonical_name, (0,), tuple(params))
        return get_parameterized_gate_matrix(g)
    return get_gate_matrix_from_map(canonical_name)


# -----------------------------------------------------------------------------
# Backend with mild realism and CZ-specific decoherence
# -----------------------------------------------------------------------------
class DummyBackend(BaseBackend):
    """Probabilistic dummy backend compatible with XEB/SPB experiments."""

    def __init__(
        self,
        cycle_fidelity: float = 0.9996,
        noise_strength: float = 1.0,
        jitter_scale: float = 0.0005,
        spam_error: float = 5e-5,
        seed: Optional[int] = 1234,
        T1: float = 5e4,
        T2: float = 3e4,
        coherent_drift: float = 0.002,
        two_qubit_boost: float = 3.0,
    ):
        super().__init__(name="UnifiedMatrixBackend")
        self.cycle_fidelity = float(cycle_fidelity)
        self.noise_strength = float(noise_strength)
        self.jitter_scale = float(jitter_scale)
        self.spam_error = float(spam_error)
        self.T1 = float(T1)
        self.T2 = float(T2)
        self.coherent_drift = float(coherent_drift)
        self.two_qubit_boost = float(two_qubit_boost)
        self.rng = np.random.default_rng(seed)

        print(
            f"[INIT] UnifiedMatrixBackend("
            f"cycle_fid={self.cycle_fidelity:.6f}, "
            f"strength={self.noise_strength:.2f}, "
            f"jitter={self.jitter_scale:.5f}, "
            f"T1={self.T1:.0f}, T2={self.T2:.0f}, "
            f"drift={self.coherent_drift:.4f}, SPAM={self.spam_error:.2e}, "
            f"CZ_boost×{self.two_qubit_boost:.1f})"
        )

    # ------------------------------------------------------------------
    def _simulate_ideal_probabilities(self, circuit: QuantumCircuit) -> np.ndarray:
        """Matrix-based statevector simulation yielding ideal probabilities."""
        n = circuit.num_qubits
        d = 2 ** n
        psi = np.zeros(d, dtype=complex)
        psi[0] = 1.0

        for g in circuit.gates:
            if getattr(g, "is_measurement", False):
                continue
            U = _gate_matrix(g.name, getattr(g, "params", []))
            qubits = g.qubits

            # Single-qubit operation
            if len(qubits) == 1:
                q = qubits[0]
                ops = [U if i == q else np.eye(2) for i in reversed(range(n))]
                U_full = ops[0]
                for u in ops[1:]:
                    U_full = np.kron(U_full, u)
            # Two-qubit operation
            elif len(qubits) == 2:
                q1, q2 = sorted(qubits)
                left = np.eye(2 ** (n - q2 - 1))
                right = np.eye(2 ** q1)
                U_full = np.kron(np.kron(left, U), right)
            # Unsupported multi-qubit (>=3)
            else:
                U_full = np.eye(d, dtype=complex)

            psi = U_full @ psi

        p = np.real(np.abs(psi) ** 2)
        p /= np.sum(p)
        return p

    # ------------------------------------------------------------------
    def _apply_physical_decay(
        self, p_ideal: np.ndarray, depth: int, has_cz: bool
    ) -> np.ndarray:
        """Apply mild depolarization, drift, and T1/T2 bias."""
        D = len(p_ideal)
        uniform = np.ones_like(p_ideal) / D

        # Base + CZ boost
        effective_strength = self.noise_strength
        if has_cz:
            effective_strength *= self.two_qubit_boost * 1.02  # small auto-tune

        eta = np.clip(
            effective_strength * (1.0 - self.cycle_fidelity ** depth), 0.0, 1.0
        )

        # T1/T2 population bias
        beta1 = np.exp(-depth / self.T1)
        beta2 = np.exp(-depth / self.T2)
        pop_bias = 0.5 * ((1 - beta1) + (1 - beta2))
        ground = np.eye(1, D, 0).ravel()
        biased = (1 - pop_bias) * p_ideal + pop_bias * ground

        # Coherent drift phase shift
        phase = self.rng.normal(0, self.coherent_drift * depth)
        drift_mix = np.roll(biased, int(D * 0.01 * np.sin(phase)))

        # Depolarization + jitter
        p_noisy = (1 - eta) * drift_mix + eta * uniform
        if self.jitter_scale > 0:
            jitter = self.rng.normal(0, self.jitter_scale * eta / D, D)
            p_noisy += jitter

        p_noisy = np.clip(p_noisy, 0, None)
        p_noisy /= np.sum(p_noisy)
        return p_noisy

    # ------------------------------------------------------------------
    def run(
        self, circuit: QuantumCircuit, shots: int = 100000
    ) -> Tuple[np.ndarray, Dict[str, int]]:
        """Simulate one circuit and return (ideal_probs, noisy_counts_dict)."""
        n = circuit.num_qubits
        D = 2 ** n
        depth = circuit.metadata.get("depth", 1)

        # Detect entangling gates
        has_cz = any(
            len(g.qubits) == 2
            and get_canonical_name(g.name) in ("cz", "iswap", "cnot")
            for g in circuit.gates
        )

        p_ideal = self._simulate_ideal_probabilities(circuit)
        p_noisy = self._apply_physical_decay(p_ideal, depth, has_cz=has_cz)

        # SPAM and sampling
        p_mix = (1 - self.spam_error) * p_noisy + self.spam_error * np.ones(D) / D
        counts = self.rng.multinomial(shots, p_mix)
        counts_dict = {
            format(i, f"0{n}b"): int(c) for i, c in enumerate(counts) if c > 0
        }
        return p_ideal.copy(), counts_dict

    # ------------------------------------------------------------------
    def execute(self, circuits: List[QuantumCircuit], shots: int = 100000):
        """Run multiple circuits sequentially (no parallelism)."""
        return [self.run(c, shots) for c in circuits]

    def execute_with_ideal(self, circuits: List[QuantumCircuit], shots: int = 100000):
        """Compatibility alias for RB/XEB engines."""
        return [self.run(c, shots) for c in circuits]

    # ------------------------------------------------------------------
    def __repr__(self):
        return (
            f"<UnifiedMatrixBackend fid={self.cycle_fidelity:.6f}, "
            f"strength={self.noise_strength:.2f}, jitter={self.jitter_scale:.5f}, "
            f"T1={self.T1:.0f}, T2={self.T2:.0f}, drift={self.coherent_drift:.4f}, "
            f"spam={self.spam_error:.2e}, cz×{self.two_qubit_boost:.1f}>"
        )