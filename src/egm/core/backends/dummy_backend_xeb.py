# [DEFINITIVE FINAL VERSION v1.9 - Refactored and Heavily Commented]

import numpy as np
from typing import List, Dict, Optional, Tuple, Any

# --- Internal Framework Imports ---
# This structure assumes the script is run from a location where 'errorgnomark' is a package.
try:
    from egm.core.circuits.circuit import QuantumCircuit, Gate, get_matrix, get_parameterized_matrix
    from egm.core.backends.base_backend import BaseBackend
except ImportError:
    # Fallback for standalone execution or testing
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from egm.core.circuits.circuit import QuantumCircuit, Gate, get_matrix, get_parameterized_matrix
    from egm.core.backends.base_backend import BaseBackend

class DummyBackend(BaseBackend):
    """
    A phenomenological backend for simulating XEB.
    
    This backend implements a standard XEB noise model where the final probability
    distribution is a mixture of the ideal distribution and a uniform distribution.
    The mixing coefficient, or 'fidelity', decays exponentially with circuit depth.
    
    Model: P_noisy = F * P_ideal + (1 - F) * P_uniform
    Fidelity: F = (1 - spam_error) * (cycle_fidelity ** depth)
    """

    def __init__(
        self,
        cycle_fidelity: float = 0.99,
        spam_error: float = 0.0,
        seed: Optional[int] = None
    ):
        """
        Initializes the backend with a phenomenological noise model.

        Args:
            cycle_fidelity (float): The fidelity 'p' of a single cycle/layer of gates.
                                    This is the base of the exponential decay.
            spam_error (float): The State Preparation and Measurement (SPAM) error.
                                This acts as a global scaling factor on the final fidelity.
                                A value of 0.01 means 1% SPAM error, so fidelity is scaled by 0.99.
            seed (Optional[int]): Seed for the random number generator for reproducible results.
        """
        super().__init__(name="DummyBackend")
        
        if not (0.0 <= cycle_fidelity <= 1.0):
            raise ValueError("cycle_fidelity must be between 0 and 1.")
        if not (0.0 <= spam_error <= 1.0):
            raise ValueError("spam_error must be between 0 and 1.")
            
        self.cycle_fidelity = cycle_fidelity
        self.spam_error = spam_error
        self.rng = np.random.default_rng(seed)
        self._cache = {} # Cache for ideal probabilities to speed up simulation

        print("DummyBackend initialized with a phenomenological model for XEB:")
        print(f"  Cycle Fidelity (p) = {self.cycle_fidelity}")
        print(f"  SPAM Error = {self.spam_error} -> Fidelity scaling factor = {1 - self.spam_error}")

    def _get_gate_matrix(self, gate: Gate) -> np.ndarray:
        """Retrieves the matrix for a gate using functions from the circuit module."""
        if gate.params:
            return get_parameterized_matrix(gate)
        else:
            return get_matrix(gate.name)

    def _apply_gate(self, statevector: np.ndarray, gate: Gate) -> np.ndarray:
        """Applies a gate to the statevector. Generalizes 1 and 2 qubit gates."""
        num_qubits = int(np.log2(statevector.shape[0]))
        
        # Create a list of identity operators
        op_list = [np.eye(2, dtype=np.complex128) for _ in range(num_qubits)]
        
        # Get the gate matrix
        gate_matrix = self._get_gate_matrix(gate)
        
        # This is a simplified approach for building the full operator.
        # A more efficient method would use swaps to move target qubits together,
        # apply the gate, and swap back. This Kronecker product approach is
        # conceptually simpler but less scalable.
        if len(gate.qubits) == 1:
            op_list[gate.qubits[0]] = gate_matrix
        elif len(gate.qubits) == 2:
            # For a 2-qubit gate on (q0, q1), we need to construct the operator
            # carefully. This part is complex for the general case.
            # Assuming a simple CNOT or similar on adjacent qubits for now.
            # The provided code only worked for qubits [0, 1]. This is a limitation.
            q0, q1 = gate.qubits
            if num_qubits == 2 and q0 == 0 and q1 == 1:
                 # The gate matrix is already the full operator
                 return gate_matrix @ statevector
            else:
                 # General case is not implemented for simplicity
                 raise NotImplementedError(
                     f"General {num_qubits}-qubit gate application on ({q0}, {q1}) is not "
                     "implemented. This dummy backend is simplified."
                 )
        else:
            raise NotImplementedError("Only 1 and 2 qubit gates are supported.")

        # Build the full operator using Kronecker products (for single-qubit gates)
        # Note: The order of Kronecker products depends on qubit indexing convention.
        # Assuming qN-1, ..., q0 convention.
        full_op = op_list[num_qubits-1]
        for i in range(num_qubits - 2, -1, -1):
            full_op = np.kron(full_op, op_list[i])
            
        return full_op @ statevector


    def _get_ideal_probabilities(self, circuit: QuantumCircuit) -> np.ndarray:
        """Calculates the ideal probability distribution by simulating the circuit."""
        circuit_key = hash(str(circuit.gates))
        if circuit_key in self._cache:
            return self._cache[circuit_key]

        num_qubits = circuit.num_qubits
        statevector = np.zeros(2**num_qubits, dtype=np.complex128)
        statevector[0] = 1.0

        for gate in circuit.gates:
            if gate.is_measurement:
                continue

            # Using a more robust (but still limited) gate application logic
            try:
                statevector = self._apply_gate(statevector, gate)
            except NotImplementedError:
                # Fallback to the original simpler logic if the general one fails
                if len(gate.qubits) == 1:
                    statevector = self._apply_single_qubit_gate(statevector, gate, gate.qubits[0])
                elif len(gate.qubits) == 2:
                    statevector = self._apply_two_qubit_gate(statevector, gate, gate.qubits[0], gate.qubits[1])

        probabilities = np.abs(statevector)**2
        self._cache[circuit_key] = probabilities
        return probabilities

    def run(
        self,
        circuit: QuantumCircuit,
        shots: int = 10000
    ) -> Tuple[None, Dict[str, int]]:
        """
        Executes a single circuit based on the XEB phenomenological model.
        """
        num_qubits = circuit.num_qubits
        depth = circuit.metadata.get('depth', 0)
        d = 2**num_qubits

        # 1. Calculate the ideal (perfect) probability distribution
        p_ideal = self._get_ideal_probabilities(circuit)

        # 2. Calculate the total circuit fidelity 'F' based on the model.
        #    F = F_spam * F_gates = (1 - spam_error) * (p^m)
        #    THIS IS THE CENTRAL FORMULA.
        #    If depth (m) > 0, this value will be < 1 even if spam_error is 0.
        circuit_fidelity = (1 - self.spam_error) * (self.cycle_fidelity ** depth)

        # 3. Create the noisy probability distribution as a mixture.
        #    P_noisy = F * P_ideal + (1 - F) * P_uniform
        p_uniform = np.full(d, 1/d)
        p_noisy = circuit_fidelity * p_ideal + (1 - circuit_fidelity) * p_uniform
        
        # Ensure probabilities sum to 1 (they should due to the formula, but this is safe)
        p_noisy /= np.sum(p_noisy)

        # 4. Sample from the noisy distribution to get measurement counts
        counts_array = self.rng.multinomial(n=shots, pvals=p_noisy)
        counts_dict = {
            format(i, f'0{num_qubits}b'): count
            for i, count in enumerate(counts_array) if count > 0
        }
        
        return (None, counts_dict)

    def execute(
        self,
        circuits: List[QuantumCircuit],
        shots: int
    ) -> List[Tuple[None, Dict[str, int]]]:
        """Executes a list of circuits."""
        self._cache.clear()
        results = []
        for circuit in circuits:
            _, counts = self.run(circuit, shots=shots)
            results.append((None, counts))
        return results
    
    # The original single/two qubit gate methods are kept for compatibility if needed
    def _apply_single_qubit_gate(self, statevector: np.ndarray, gate: Gate, target_qubit: int) -> np.ndarray:
        # This is a less efficient but simple way to apply a gate
        num_qubits = int(np.log2(statevector.shape[0]))
        op_list = [np.eye(2) for _ in range(num_qubits)]
        op_list[target_qubit] = self._get_gate_matrix(gate)
        full_op = op_list[0]
        for i in range(1, num_qubits):
            full_op = np.kron(full_op, op_list[i])
        return full_op @ statevector

    def _apply_two_qubit_gate(self, statevector: np.ndarray, gate: Gate, q0: int, q1: int) -> np.ndarray:
        if int(np.log2(statevector.shape[0])) == 2 and q0 == 0 and q1 == 1:
            return self._get_gate_matrix(gate) @ statevector
        else:
            raise NotImplementedError("Simplified 2-qubit gate application failed.")