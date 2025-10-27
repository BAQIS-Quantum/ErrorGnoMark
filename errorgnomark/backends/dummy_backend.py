# File Path: errorgnomark/backends/dummy_backend.py
#
# [ULTIMATE COMPATIBILITY v4.0 - Dual-Mode PRB & General-Purpose Model]

import numpy as np
from typing import List, Dict, Optional, Tuple, Any

# --- Internal Framework Imports ---
try:
    from .base_backend import BaseBackend
    from ..circuits.circuit import QuantumCircuit
except ImportError:
    # Fallback for standalone execution or testing
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from errorgnomark.circuits.circuit import QuantumCircuit
    from errorgnomark.backends.base_backend import BaseBackend

class DummyBackend(BaseBackend):
    """
    A universal phenomenological backend that intelligently simulates quantum circuits
    for various benchmarking protocols.

    This backend operates in two modes, automatically selected based on circuit metadata:
    
    1.  **PRB Mode**: Activated if `circuit.metadata` contains the key 'is_twirled_circuit'.
        It uses a specialized model for Purity Randomized Benchmarking, relying on
        `clifford_fidelity` and distinguishing between twirled (A) and non-twirled (B)
        circuits. This is compatible with the `PRBExperiment`.

    2.  **General-Purpose Mode**: Used for all other circuits (e.g., from SPB, XEB).
        It applies a standard depolarizing noise model, calculating fidelity by
        iterating through each gate in the circuit, based on `depolarizing_error_1q`
        and `depolarizing_error_2q`.

    [V4.0 ChangeLog]
    - UNIFIED: Merged the PRB-specific model (v2.0) and the general-purpose depolarizing
      model (v3.0) into a single, intelligent class.
    - AUTO-DETECTION: The `run` method now checks for `'is_twirled_circuit'` in metadata
      to decide which noise model to apply.
    - FULL COMPATIBILITY: This backend now works seamlessly with PRB, SPB, and XEB
      experiments without requiring any changes to the experiment scripts.
    """

    def __init__(
        self,
        # General-purpose model parameters (for SPB, XEB, etc.)
        depolarizing_error_1q: float = 0.001,
        depolarizing_error_2q: float = 0.01,
        
        # PRB-specific model parameters
        clifford_fidelity: float = 0.99,
        gate_fidelities: Optional[Dict[str, float]] = None,
        
        # Common parameters
        spam_error_rate: float = 0.01,
        seed: Optional[int] = None
    ):
        super().__init__(name="DummyBackend")
        
        # Store all parameters for both models
        self.fidelity_1q = 1.0 - depolarizing_error_1q
        self.fidelity_2q = 1.0 - depolarizing_error_2q
        self.clifford_fidelity = clifford_fidelity
        self.gate_fidelities = gate_fidelities if gate_fidelities is not None else {}
        self.spam_error_rate = spam_error_rate
        self.rng = np.random.default_rng(seed)

        # SPAM parameters used by both models (for non-twirled circuits)
        self.A_spam = 1.0 - spam_error_rate
        self.B_spam = spam_error_rate

        print("=" * 50)
        print("DummyBackend v4.0 (Universal Dual-Mode) Initialized")
        print("-" * 50)
        print("  General-Purpose Model (for SPB, XEB):")
        print(f"    1Q Gate Fidelity = {self.fidelity_1q:.4f} (Error = {depolarizing_error_1q:.1e})")
        print(f"    2Q Gate Fidelity = {self.fidelity_2q:.4f} (Error = {depolarizing_error_2q:.1e})")
        print("-" * 50)
        print("  PRB Model:")
        print(f"    1Q Clifford Fidelity p_C1 = {self.clifford_fidelity}")
        if self.gate_fidelities:
            print(f"    Specific Gate Fidelities p_G = {self.gate_fidelities}")
        print("-" * 50)
        print("  Common Parameters:")
        print(f"    SPAM Error Rate = {self.spam_error_rate:.4f}")
        print("=" * 50)


    def run(
        self,
        circuit: QuantumCircuit,
        shots: Optional[int] = 1000
    ) -> Tuple[Any, Optional[Dict[str, int]]]:
        """
        Executes a circuit by auto-detecting the experiment type and applying
        the corresponding noise model.
        """
        num_qubits = circuit.num_qubits
        d = 2**num_qubits
        survival_prob = 0.0

        # --- AUTO-DETECTION LOGIC ---
        is_prb_circuit = 'is_twirled_circuit' in circuit.metadata

        if is_prb_circuit:
            # --- MODE 1: PRB EXPERIMENT ---
            depth = circuit.metadata.get('depth')
            if depth is None:
                raise ValueError("PRB circuit metadata must contain a 'depth' key.")
            
            interleaved_gate_name = circuit.metadata.get('interleaved_gate_name')
            is_circuit_a = circuit.metadata.get('is_twirled_circuit', False)

            # Calculate decay parameter 'p' for one Clifford layer
            p = self.clifford_fidelity
            if num_qubits > 1:
                cnot_fidelity = self.gate_fidelities.get('CNOT')
                if cnot_fidelity is None:
                    raise ValueError("DummyBackend in PRB mode requires 'CNOT' fidelity for 2Q experiments.")
                p *= cnot_fidelity

            if interleaved_gate_name:
                gate_fidelity = self.gate_fidelities.get(interleaved_gate_name)
                if gate_fidelity is None:
                    raise ValueError(f"DummyBackend lacks fidelity for interleaved gate '{interleaved_gate_name}'.")
                p *= gate_fidelity

            if is_circuit_a:
                # Circuit A (twirled): survival probability is ideally 0.5
                survival_prob = 0.5
            else:
                # Circuit B (baseline): decays exponentially
                survival_prob = self.A_spam * (p ** depth) + self.B_spam

        else:
            # --- MODE 2: GENERAL-PURPOSE EXPERIMENT (SPB, XEB, etc.) ---
            circuit_fidelity = 1.0
            for gate in circuit.gates:
                num_gate_qubits = len(gate.qubits)
                if num_gate_qubits == 1:
                    circuit_fidelity *= self.fidelity_1q
                elif num_gate_qubits == 2:
                    circuit_fidelity *= self.fidelity_2q
            
            # P(survival) = F + (1-F)/d
            survival_prob_no_spam = circuit_fidelity + (1.0 - circuit_fidelity) / d
            
            # Apply SPAM error
            survival_prob = survival_prob_no_spam * (1.0 - self.spam_error_rate) \
                          + (1.0 / d) * self.spam_error_rate

        # --- COMMON SIMULATION STEP ---
        # Simulate measurement outcomes based on the calculated survival probability
        survival_prob = np.clip(survival_prob, 0.0, 1.0)
        num_success = self.rng.binomial(n=shots, p=survival_prob)

        ground_state_str = '0' * num_qubits
        other_state_str = '1' * num_qubits
        
        counts = {
            ground_state_str: num_success,
            other_state_str: shots - num_success
        }
        
        return (None, counts)

    def execute(
        self,
        circuits: List[QuantumCircuit],
        shots: int
    ) -> List[Tuple[None, Dict[str, int]]]:
        """Executes a batch of circuits."""
        return [self.run(c, shots) for c in circuits]