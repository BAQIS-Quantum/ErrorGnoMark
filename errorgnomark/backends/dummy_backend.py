# File Path: errorgnomark/backends/dummy_backend.py
# [DEFINITIVE FINAL VERSION v4 - Fully compatible with the new BaseBackend API]

import numpy as np
from typing import Dict, Tuple, List

# Use the new, correct BaseBackend
try:
    from errorgnomark.backends.base_backend import BaseBackend
    from errorgnomark.circuits.circuit import QuantumCircuit, Gate
    from errorgnomark.circuits.circuit import get_matrix as get_gate_matrix_from_map
    from errorgnomark.circuits.circuit import get_parameterized_matrix as get_parameterized_gate_matrix
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from errorgnomark.backends.base_backend import BaseBackend
    from errorgnomark.circuits.circuit import QuantumCircuit, Gate
    from errorgnomark.circuits.circuit import get_matrix as get_gate_matrix_from_map
    from errorgnomark.circuits.circuit import get_parameterized_matrix as get_parameterized_gate_matrix

class DummyBackend(BaseBackend):
    """
    An advanced dummy backend with a robust noise model, fully compliant with BaseBackend.
    """
    
    def __init__(self, **kwargs):
        defaults = {
            'depolarizing_error_1q': 0.001,
            'depolarizing_error_2q': 0.01,
            'spam_error': 0.0,
        }
        # Special handling for gate-specific errors
        self.special_errors = {k: v for k, v in kwargs.items() if k.endswith('_error')}
        
        self.depolarizing_error_1q = self.special_errors.pop('depolarizing_error_1q', defaults['depolarizing_error_1q'])
        self.depolarizing_error_2q = self.special_errors.pop('depolarizing_error_2q', defaults['depolarizing_error_2q'])
        self.spam_error = self.special_errors.pop('spam_error', defaults['spam_error'])
        
        print(f"DummyBackend initialized with default errors (1Q: {self.depolarizing_error_1q}, 2Q: {self.depolarizing_error_2q}, SPAM: {self.spam_error}) "
              f"and special gate errors: {self.special_errors}")

    def _get_depolarizing_rate(self, gate: Gate) -> float:
        """Determines the depolarizing error rate for a specific gate."""
        gate_error_key = f"{gate.name.lower()}_error"
        if gate_error_key in self.special_errors:
            return self.special_errors[gate_error_key]
        
        if gate.arity == 1:
            return self.depolarizing_error_1q
        elif gate.arity == 2:
            return self.depolarizing_error_2q
        else:
            return 0.0

    # <<< FIX #1: Robustly handles ALL gate types (parameterized and non-parameterized) >>>
    def _get_ideal_gate_matrix(self, gate: Gate) -> np.ndarray:
        """
        Retrieves the ideal unitary matrix for a given gate.
        """
        if gate.name.lower() == 'measure':
            return np.eye(2**len(gate.qubits), dtype=complex)
            
        try:
            if gate.params:
                # This is a parameterized gate, use the specific constructor from circuit.py
                return get_parameterized_gate_matrix(gate)
            else:
                # This is a non-parameterized gate, look it up in the map
                return get_gate_matrix_from_map(gate.name)
        except ValueError as e:
            # This will catch errors from both functions if the gate is truly unknown
            raise ValueError(f"Gate '{gate.name}' is not recognized by the backend.") from e

    def _get_permutation_matrix(self, permutation: List[int], num_qubits: int) -> np.ndarray:
        dim = 2**num_qubits; basis_indices = np.arange(dim)
        binary_basis = (((basis_indices[:, None] & (1 << np.arange(num_qubits - 1, -1, -1))) > 0)).astype(int)
        permuted_binary_basis = binary_basis[:, permutation]
        permuted_indices = (permuted_binary_basis * (1 << np.arange(num_qubits - 1, -1, -1))).sum(axis=1)
        P = np.zeros((dim, dim), dtype=int); P[permuted_indices, basis_indices] = 1; return P

    def _simulate_statevector(self, circuit: QuantumCircuit) -> np.ndarray:
        num_qubits = len(circuit.qubits); qubit_to_pos = {qubit: i for i, qubit in enumerate(circuit.qubits)}
        state_vector = np.zeros(2**num_qubits, dtype=complex); state_vector[0] = 1.0
        for gate in circuit.gates:
            if gate.name.lower() == 'measure': continue
            
            gate_matrix_to_apply = self._get_ideal_gate_matrix(gate)
            num_gate_qubits = len(gate.qubits)
            
            target_pos = [qubit_to_pos[q] for q in gate.qubits]; other_pos = [i for i in range(num_qubits) if i not in target_pos]
            permutation = target_pos + other_pos; P = self._get_permutation_matrix(permutation, num_qubits)
            
            identity_part = np.eye(2**(num_qubits - num_gate_qubits))
            full_op = np.kron(gate_matrix_to_apply, identity_part); final_operator = P.T @ full_op @ P
            state_vector = final_operator @ state_vector
        return state_vector

    def _get_probabilities_from_statevector(self, state_vector: np.ndarray) -> Dict[str, float]:
        num_qubits = int(np.log2(len(state_vector))); probabilities = np.abs(state_vector)**2
        return {format(i, f'0{num_qubits}b'): prob for i, prob in enumerate(probabilities)}

    def _sample_from_probabilities(self, probabilities: Dict[str, float], shots: int) -> Dict[str, int]:
        if not probabilities: return {}
        bitstrings, probs = list(probabilities.keys()), list(probabilities.values())
        probs_sum = np.sum(probs)
        if not np.isclose(probs_sum, 1.0) and probs_sum > 0: probs = np.array(probs) / probs_sum
        elif probs_sum <= 0: return {b: 0 for b in bitstrings}
        if len(bitstrings) == 0: return {}
        samples = np.random.choice(bitstrings, size=shots, p=probs)
        unique_samples, counts = np.unique(samples, return_counts=True)
        counts_dict = dict(zip(unique_samples, counts))
        return counts_dict

    def run(self, circuit: QuantumCircuit, shots: int) -> Tuple[Dict[str, float], Dict[str, int]]:
        num_qubits = len(circuit.qubits); d = 2**num_qubits

        # 1. Simulate the ideal statevector to get the ideal probability distribution.
        ideal_statevector = self._simulate_statevector(circuit)
        ideal_probabilities = self._get_probabilities_from_statevector(ideal_statevector)

        # 2. Calculate the total depolarizing survival probability.
        survival_prob = 1.0
        for gate in circuit.gates:
            if not gate.is_measurement:
                p = self._get_depolarizing_rate(gate)
                survival_prob *= (1.0 - p)
        
        # 3. Create the noisy distribution by mixing the ideal distribution with a uniform one.
        e = 1.0 - survival_prob # Total depolarizing error
        probs_after_depolarizing = {}
        if e > 1e-15:
            uniform_prob_per_state = e / d
            for bitstring, prob in ideal_probabilities.items():
                probs_after_depolarizing[bitstring] = (1 - e) * prob + uniform_prob_per_state
        else:
            probs_after_depolarizing = ideal_probabilities

        # 4. Apply SPAM error as the final step.
        final_noisy_probabilities = {}
        spam_e = self.spam_error
        if spam_e > 1e-15:
            M_1q = np.array([[1 - spam_e, spam_e], [spam_e, 1 - spam_e]]); M_total = M_1q
            for _ in range(num_qubits - 1): M_total = np.kron(M_total, M_1q)
            prob_vector = np.array([probs_after_depolarizing.get(format(i, f'0{num_qubits}b'), 0.0) for i in range(d)])
            observed_prob_vector = M_total @ prob_vector
            final_noisy_probabilities = {format(i, f'0{num_qubits}b'): p for i, p in enumerate(observed_prob_vector)}
        else:
            final_noisy_probabilities = probs_after_depolarizing

        # 5. Sample from the final noisy distribution to get counts.
        noisy_counts = self._sample_from_probabilities(final_noisy_probabilities, shots)
        
        # <<< FIX #2: Return value now matches the BaseBackend interface perfectly >>>
        return final_noisy_probabilities, noisy_counts