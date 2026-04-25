from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from egm.foundation.backends.base_backend import BaseBackend
from egm.foundation.circuits.circuit import QuantumCircuit


class DummyBackend(BaseBackend):
    """
    Backend for end-to-end testing of CZ Enhanced CSB.

    This backend is not a physical simulator. It implements the
    idealized signal model assumed by Enhanced CSB analysis:

        <Ox>(n) = A · r^n · cos(n · φ)
        <Oy>(n) = A · r^n · sin(n · φ)

    The purpose of this backend is validation of the circuit execution
    and analysis pipeline, not hardware modeling.
    """

    def __init__(
        self,
        *,
        cz_phase: float = 0.3,
        decay_rate: float = 0.97,
        contrast: float = 0.9,
        baseline: float = 0.0,
        spam_error: float = 0.0,
        seed: Optional[int] = None,
    ):
        super().__init__(name="EnhancedCSBTestBackend")

        self.phi = float(cz_phase)
        self.r = float(decay_rate)
        self.contrast = float(contrast)
        self.baseline = float(baseline)
        self.spam = float(spam_error)
        self.rng = np.random.default_rng(seed)

        print("[EnhancedCSBTestBackend] Initialized (E2E test mode)")
        print(f"  True phase φ : {self.phi:.6f} rad")
        print(f"  Decay rate r : {self.r:.6f}")

    def run(
        self,
        circuit: QuantumCircuit,
        shots: int = 1024,
    ) -> Tuple[Any, Dict[str, int]]:
        """
        Execute a single CSB circuit.

        The backend reads circuit metadata only:
            - csb_index (depth index)
            - observable: "ox" or "oy"
        """
        meta = circuit.metadata or {}

        if meta.get("experiment_type") != "CSB-CZ-Enhanced":
            raise RuntimeError(
                "EnhancedCSBTestBackend only supports CSB-CZ-Enhanced experiments"
            )

        n = meta.get("csb_index")
        observable = meta.get("observable")

        if n is None or observable not in ("ox", "oy"):
            raise RuntimeError("Missing csb_index or observable in circuit metadata")

        if observable == "ox":
            expectation = self.contrast * (self.r ** n) * np.cos(n * self.phi)
        else:
            expectation = self.contrast * (self.r ** n) * np.sin(n * self.phi)

        expectation += self.baseline
        expectation = float(np.clip(expectation, -1.0, 1.0))

        p_even = 0.5 * (1.0 + expectation)
        p_even = p_even * (1.0 - self.spam) + 0.5 * self.spam
        p_even = float(np.clip(p_even, 0.0, 1.0))

        n_even = self.rng.binomial(n=shots, p=p_even)
        n_odd = shots - n_even

        return None, {
            "00": n_even // 2,
            "11": n_even - (n_even // 2),
            "01": n_odd // 2,
            "10": n_odd - (n_odd // 2),
        }

    def execute(
        self,
        circuits: List[QuantumCircuit],
        shots: int,
    ) -> List[Tuple[Any, Dict[str, int]]]:
        return [self.run(circuit, shots) for circuit in circuits]


# -----------------------------------------------------------------------------
# Data generation and modeling notes
# -----------------------------------------------------------------------------
#
# This backend generates synthetic CSB measurement data using an analytic
# signal model rather than simulating quantum state evolution.
#
# 1. Signal model
#    For each circuit depth n, ideal expectation values are generated as
#
#        <Ox>(n) = A · r^n · cos(n · φ)
#        <Oy>(n) = A · r^n · sin(n · φ)
#
#    where φ is the true CZ phase, r is the dominant spectral decay factor,
#    and A is a contrast prefactor.
#
# 2. Measurement interpretation
#    Expectation values are interpreted as parity expectations after
#    basis rotation, i.e. <Z⊗Z>. The relation
#
#        p_even − p_odd = <Z⊗Z>
#
#    is used to convert expectations into bitstring probabilities.
#
# 3. Sampling and noise
#    Finite-shot sampling is applied via a binomial distribution.
#    Optional SPAM noise mixes the parity probability toward 0.5.
#
# 4. Scope and limitations
#    - No coherent over-rotation, leakage, or non-Markovian effects
#      are modeled.
#    - The decay parameter r is interpreted as a dominant PTM eigenvalue
#      magnitude, consistent with the CSB analysis assumptions.
#    - This backend is intended for validation and regression testing
#      only, not for physical accuracy.
#