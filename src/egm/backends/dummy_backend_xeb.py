# =============================================================================
# File    : egm/backends/dummy_backend_xeb.py
# Version : v5.3.0 - UnifiedMatrixBackend (matrix noise for XEB/SPB smoke)
# =============================================================================
"""
Matrix-based noisy simulator backend for XEB / SPB workflows.

- Propagates pure state via gate matrices from `egm.circuits.circuit`.
- Applies mild depolarization, T1/T2 bias, coherent drift, and multinomial sampling.
- `Executor` still computes its own ideal reference via `IdealBackend`; only the
  **noisy counts** tuple element from `run()` is consumed for that path.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

from egm.backends.base_backend import BaseBackend
from egm.circuits.circuit import (
    Gate,
    QuantumCircuit,
    get_canonical_name,
    get_matrix,
    get_parameterized_matrix,
)

logger = logging.getLogger(__name__)


def _gate_unitary(g: Gate) -> np.ndarray:
    """Unitary for one gate, using canonical name and params."""
    canonical = get_canonical_name(g.name)
    if g.params:
        gg = Gate(canonical, g.qubits, g.params)
        return get_parameterized_matrix(gg)
    return get_matrix(canonical)


class DummyBackend(BaseBackend):
    """Probabilistic matrix backend compatible with XEB/SPB experiments."""

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
    ) -> None:
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

        logger.debug(
            "UnifiedMatrixBackend init cycle_fid=%s strength=%s jitter=%s "
            "T1=%s T2=%s drift=%s spam=%s cz_boost=%s seed=%s",
            self.cycle_fidelity,
            self.noise_strength,
            self.jitter_scale,
            self.T1,
            self.T2,
            self.coherent_drift,
            self.spam_error,
            self.two_qubit_boost,
            seed,
        )

    def _simulate_ideal_probabilities(self, circuit: QuantumCircuit) -> np.ndarray:
        """Matrix-based statevector simulation yielding measurement probabilities."""
        n = circuit.num_qubits
        d = 2**n
        psi = np.zeros(d, dtype=complex)
        psi[0] = 1.0

        for g in circuit.gates:
            if g.is_measurement:
                continue
            u_gate = _gate_unitary(g)
            targets = list(g.qubits)

            if len(targets) == 1:
                q = targets[0]
                ops = [
                    u_gate if idx == q else np.eye(2) for idx in reversed(range(n))
                ]
                u_full = ops[0]
                for u in ops[1:]:
                    u_full = np.kron(u_full, u)
            elif len(targets) == 2:
                q1, q2 = sorted(targets)
                left = np.eye(2 ** (n - q2 - 1))
                right = np.eye(2**q1)
                u_full = np.kron(np.kron(left, u_gate), right)
            else:
                u_full = np.eye(d, dtype=complex)

            psi = u_full @ psi

        p = np.real(np.abs(psi) ** 2)
        p /= np.sum(p)
        return p

    def _apply_physical_decay(
        self, p_ideal: np.ndarray, depth: int, has_cz: bool
    ) -> np.ndarray:
        """Apply mild depolarization, drift, and T1/T2 bias."""
        d = len(p_ideal)
        uniform = np.ones_like(p_ideal) / d

        effective_strength = self.noise_strength
        if has_cz:
            effective_strength *= self.two_qubit_boost * 1.02

        eta = np.clip(
            effective_strength * (1.0 - self.cycle_fidelity**depth), 0.0, 1.0
        )

        beta1 = np.exp(-depth / self.T1)
        beta2 = np.exp(-depth / self.T2)
        pop_bias = 0.5 * ((1 - beta1) + (1 - beta2))
        ground = np.eye(1, d, 0).ravel()
        biased = (1 - pop_bias) * p_ideal + pop_bias * ground

        phase = self.rng.normal(0, self.coherent_drift * depth)
        drift_mix = np.roll(biased, int(d * 0.01 * np.sin(phase)))

        p_noisy = (1 - eta) * drift_mix + eta * uniform
        if self.jitter_scale > 0:
            jitter = self.rng.normal(0, self.jitter_scale * eta / d, d)
            p_noisy += jitter

        p_noisy = np.clip(p_noisy, 0, None)
        p_noisy /= np.sum(p_noisy)
        return p_noisy

    def run(
        self,
        circuit: QuantumCircuit,
        shots: Optional[int] = None,
    ) -> Tuple[np.ndarray, Dict[str, int]]:
        """Return (ideal distribution from this model, sampled counts dict)."""
        n = circuit.num_qubits
        d = 2**n
        shots_i = int(shots or 100_000)
        depth = int(circuit.metadata.get("depth", 1))

        has_cz = any(
            len(g.qubits) == 2
            and get_canonical_name(g.name) in ("cz", "iswap", "cnot")
            for g in circuit.gates
        )

        p_ideal = self._simulate_ideal_probabilities(circuit)
        p_noisy = self._apply_physical_decay(p_ideal, depth, has_cz=has_cz)

        p_mix = (1 - self.spam_error) * p_noisy + self.spam_error * np.ones(d) / d
        counts = self.rng.multinomial(shots_i, p_mix)
        counts_dict = {
            format(i, f"0{n}b"): int(c) for i, c in enumerate(counts) if c > 0
        }
        return p_ideal.copy(), counts_dict

    def execute(self, circuits: List[QuantumCircuit], shots: int = 100_000):
        """Run multiple circuits sequentially."""
        return [self.run(c, shots) for c in circuits]

    def execute_with_ideal(self, circuits: List[QuantumCircuit], shots: int = 100_000):
        """Compatibility alias for benchmarking engines."""
        return [self.run(c, shots) for c in circuits]

    def __repr__(self) -> str:
        return (
            f"<UnifiedMatrixBackend fid={self.cycle_fidelity:.6f}, "
            f"strength={self.noise_strength:.2f}, jitter={self.jitter_scale:.5f}, "
            f"T1={self.T1:.0f}, T2={self.T2:.0f}, drift={self.coherent_drift:.4f}, "
            f"spam={self.spam_error:.2e}, cz×{self.two_qubit_boost:.1f}>"
        )


# Backward-friendly alias
UnifiedMatrixBackend = DummyBackend
