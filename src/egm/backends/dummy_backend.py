# File: errorgnomark/backends/dummy_backend.py
# ---------------------------------------------------------------------
# Module: DummyBackend — Universal Dual‑Mode Noisy Quantum Backend
# ---------------------------------------------------------------------
# This backend provides a fast, phenomenological simulation environment
# for various benchmarking experiments such as RB, PRB, SPB, and XEB.
#
# It automatically determines the appropriate noise model based on the
# circuit metadata, supporting two operation modes:
#   1. PRB Mode: Activated when `is_twirled_circuit` appears in metadata.
#   2. General‑Purpose Mode: Applied to all other circuits.
#
# Version: 4.0  •  Unified PRB + Depolarizing Model
# ---------------------------------------------------------------------

from __future__ import annotations
import numpy as np
from typing import List, Dict, Optional, Tuple, Any

# ---------------------------------------------------------------------
# Internal Framework Imports
# ---------------------------------------------------------------------
try:
    from egm.foundation.backends.base_backend import BaseBackend
    from egm.foundation.circuits.circuit import QuantumCircuit
except ImportError:
    import sys
    import os

    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    )
    from egm.foundation.circuits.circuit import QuantumCircuit
    from egm.foundation.backends.base_backend import BaseBackend


# ---------------------------------------------------------------------
# DummyBackend Definition
# ---------------------------------------------------------------------
class DummyBackend(BaseBackend):
    """
    A configurable phenomenological backend that simulates noisy circuit
    execution for benchmarking and characterization experiments.

    **Dual-Mode Behavior**

    - **PRB Mode**: Activated if `circuit.metadata` contains
      `'is_twirled_circuit'`. This mode implements a purity randomized
      benchmarking (PRB) decay model using the given Clifford and
      optional gate fidelities.

    - **General-Purpose Mode**: Default mode for all other circuit types.
      Uses a standard depolarizing noise model with per-gate fidelity
      parameters.

    The backend generates measurement count dictionaries consistent with
    experimental expectations, including optional SPAM errors.
    """

    # -----------------------------------------------------------------
    # Initialization
    # -----------------------------------------------------------------
    def __init__(
        self,
        depolarizing_error_1q: float = 0.001,
        depolarizing_error_2q: float = 0.01,
        clifford_fidelity: float = 0.99,
        gate_fidelities: Optional[Dict[str, float]] = None,
        spam_error_rate: float = 0.01,
        seed: Optional[int] = None,
    ):
        """
        Initialize a dual-mode DummyBackend.

        Args:
            depolarizing_error_1q: Depolarizing error rate for single-qubit gates.
            depolarizing_error_2q: Depolarizing error rate for two-qubit gates.
            clifford_fidelity: Average Clifford gate fidelity (used in PRB mode).
            gate_fidelities: Optional dictionary of per-gate fidelities.
            spam_error_rate: State Preparation and Measurement (SPAM) error rate.
            seed: Optional random seed for deterministic reproducibility.
        """
        super().__init__(name="DummyBackend")

        # Derived fidelity values
        self.fidelity_1q = 1.0 - depolarizing_error_1q
        self.fidelity_2q = 1.0 - depolarizing_error_2q
        self.clifford_fidelity = clifford_fidelity
        self.gate_fidelities = gate_fidelities or {}
        self.spam_error_rate = spam_error_rate
        self.rng = np.random.default_rng(seed)

        # SPAM model constants
        self.A_spam = 1.0 - spam_error_rate
        self.B_spam = spam_error_rate

        # Brief initialization output
        print("[DummyBackend] Initialized (v4.0, dual-mode)")
        print(f"  Single-qubit fidelity:   {self.fidelity_1q:.4f}")
        print(f"  Two-qubit fidelity:      {self.fidelity_2q:.4f}")
        print(f"  Clifford fidelity (PRB): {self.clifford_fidelity:.4f}")
        print(f"  SPAM error rate:         {self.spam_error_rate:.4f}")

    # -----------------------------------------------------------------
    # Core Execution
    # -----------------------------------------------------------------
    def run(
        self, circuit: QuantumCircuit, shots: Optional[int] = 1000
    ) -> Tuple[Any, Dict[str, int]]:
        """
        Execute a single quantum circuit with noise sampling.

        Automatically chooses between the PRB model and the general
        depolarizing model depending on circuit metadata.

        Args:
            circuit: Quantum circuit to execute.
            shots: Number of simulated measurement repetitions.

        Returns:
            Tuple of (statevector, counts). For this phenomenological
            backend, the statevector is always `None`.
        """
        num_qubits = circuit.num_qubits
        dim = 2**num_qubits
        survival_prob = 0.0

        # Auto-select model
        is_prb = "is_twirled_circuit" in circuit.metadata

        if is_prb:
            # ---------------------------------------------------------
            # Mode 1: PRB Experiment
            # ---------------------------------------------------------
            depth = circuit.metadata.get("depth")
            if depth is None:
                raise ValueError("PRB circuit metadata must include 'depth'.")

            is_twirled = circuit.metadata.get("is_twirled_circuit", False)
            interleaved_gate = circuit.metadata.get("interleaved_gate_name")

            p = self.clifford_fidelity
            # Adjust fidelity for multi-qubit Clifford or interleaved gate
            if num_qubits > 1:
                cnot_fid = self.gate_fidelities.get("CNOT")
                if cnot_fid is None:
                    raise ValueError(
                        "PRB mode requires a 'CNOT' fidelity value for two-qubit runs."
                    )
                p *= cnot_fid
            if interleaved_gate:
                gfid = self.gate_fidelities.get(interleaved_gate)
                if gfid is None:
                    raise ValueError(
                        f"Missing fidelity for interleaved gate '{interleaved_gate}'."
                    )
                p *= gfid

            # Compute survival probability
            if is_twirled:
                survival_prob = 0.5  # Twirled circuit baseline
            else:
                survival_prob = self.A_spam * (p**depth) + self.B_spam

        else:
            # ---------------------------------------------------------
            # Mode 2: General-Purpose Benchmarking (RB, SPB, XEB)
            # ---------------------------------------------------------
            circuit_fidelity = 1.0
            for gate in circuit.gates:
                n_q = len(gate.qubits)
                if n_q == 1:
                    circuit_fidelity *= self.fidelity_1q
                elif n_q == 2:
                    circuit_fidelity *= self.fidelity_2q

            # Depolarizing fidelity model
            survival_ideal = circuit_fidelity + (1.0 - circuit_fidelity) / dim

            # Apply SPAM
            survival_prob = (
                survival_ideal * (1.0 - self.spam_error_rate)
                + (1.0 / dim) * self.spam_error_rate
            )

        # -------------------------------------------------------------
        # Measurement Simulation
        # -------------------------------------------------------------
        survival_prob = np.clip(survival_prob, 0.0, 1.0)
        successful = self.rng.binomial(n=shots, p=survival_prob)

        ground_state = "0" * num_qubits
        other_state = "1" * num_qubits

        counts = {
            ground_state: successful,
            other_state: shots - successful,
        }

        return (None, counts)

    # -----------------------------------------------------------------
    # Batch Execution
    # -----------------------------------------------------------------
    def execute(
        self, circuits: List[QuantumCircuit], shots: int
    ) -> List[Tuple[None, Dict[str, int]]]:
        """
        Execute a batch of circuits sequentially.

        Args:
            circuits: List of quantum circuits to execute.
            shots: Number of measurement repetitions per circuit.

        Returns:
            List of `(None, counts)` tuples for each circuit.
        """
        return [self.run(circuit, shots) for circuit in circuits]