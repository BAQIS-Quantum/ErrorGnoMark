# File Path: errorgnomark/backends/dummy_backend.py
# This is the complete, user-provided backend code.

import numpy as np
from typing import Dict, Tuple, List, Optional
import warnings

try:
    from errorgnomark.backends.base_backend import BaseBackend
    from errorgnomark.circuits.circuit import QuantumCircuit, Gate
    from errorgnomark.circuits.circuit import get_matrix as get_gate_matrix_from_map
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from errorgnomark.backends.base_backend import BaseBackend
    from errorgnomark.circuits.circuit import QuantumCircuit, Gate
    from errorgnomark.circuits.circuit import get_matrix as get_gate_matrix_from_map

class DummyBackend(BaseBackend):
    """
    An advanced dummy backend with a backward-compatible, realistic noise model.
    This backend simulates a hierarchy of errors and supports both legacy and
    current parameter names for instantiation.
    """
    
    def __init__(self, **kwargs):
        """
        Initializes the backend with a flexible set of error parameters.
        """
        defaults = {
            'depolarizing_error_1q': 0.001,
            'depolarizing_error_2q': 0.01,
            'spam_error': 0.0,
            'coherent_1q_error_angle': 0.0,
            'coherent_2q_error_angle': 0.0,
        }

        if 'depolarizing_error' in kwargs:
            warnings.warn(
                "'depolarizing_error' is a legacy parameter. It is being applied to both "
                "'depolarizing_error_1q' and 'depolarizing_error_2q'. For more precise control, "
                "please use the new parameters.",
                DeprecationWarning,
                stacklevel=2
            )
            old_dep_error = kwargs.pop('depolarizing_error')
            defaults['depolarizing_error_1q'] = old_dep_error
            defaults['depolarizing_error_2q'] = old_dep_error

        if 'gate_angle_error' in kwargs:
            warnings.warn(
                "'gate_angle_error' is a legacy parameter. It is being mapped to "
                "'coherent_1q_error_angle'.",
                DeprecationWarning,
                stacklevel=2
            )
            defaults['coherent_1q_error_angle'] = kwargs.pop('gate_angle_error')

        if 'systematic_theta_error' in kwargs or 'systematic_phi_error' in kwargs:
             warnings.warn(
                "'systematic_theta_error' and 'systematic_phi_error' are legacy parameters "
                "for a different 2Q coherent error model and are now ignored. Please use "
                "'coherent_2q_error_angle' for the Rzz error model.",
                DeprecationWarning,
                stacklevel=2
            )
             kwargs.pop('systematic_theta_error', None)
             kwargs.pop('systematic_phi_error', None)

        self.depolarizing_error_1q = kwargs.get('depolarizing_error_1q', defaults['depolarizing_error_1q'])
        self.depolarizing_error_2q = kwargs.get('depolarizing_error_2q', defaults['depolarizing_error_2q'])
        self.spam_error = kwargs.get('spam_error', defaults['spam_error'])
        self.coherent_1q_error_angle = kwargs.get('coherent_1q_error_angle', defaults['coherent_1q_error_angle'])
        self.coherent_2q_error_angle = kwargs.get('coherent_2q_error_angle', defaults['coherent_2q_error_angle'])

        if not (0 <= self.depolarizing_error_1q <= 1): raise ValueError("1Q Depolarizing error must be between 0 and 1.")
        if not (0 <= self.depolarizing_error_2q <= 1): raise ValueError("2Q Depolarizing error must be between 0 and 1.")
        if not (0 <= self.spam_error <= 1): raise ValueError("SPAM error must be between 0 and 1.")

    def _get_ideal_gate_matrix(self, gate: Gate) -> np.ndarray:
        if gate.name == "matrix_gate":
            if gate.params and isinstance(gate.params[0], np.ndarray): return gate.params[0]
            raise ValueError("Gate 'matrix_gate' is missing its matrix in params.")
        gate_name = gate.name.lower()
        if gate_name == 'ry':
            if not gate.params: raise ValueError("RY gate requires a 'theta' parameter.")
            theta = gate.params[0]; c, s = np.cos(theta / 2), np.sin(theta / 2); return np.array([[c, -s], [s, c]], dtype=complex)
        if gate_name == 'cry':
            if not gate.params: raise ValueError("CRY gate requires a 'theta' parameter.")
            theta = gate.params[0]; c, s = np.cos(theta / 2), np.sin(theta / 2); return np.array([[1,0,0,0], [0,1,0,0], [0,0,c,-s], [0,0,s,c]], dtype=complex)
        if gate.name.lower() == 'measure': return np.eye(2**len(gate.qubits), dtype=complex)
        try: return get_gate_matrix_from_map(gate.name)
        except ValueError as e: raise ValueError(f"Gate '{gate.name}' is not recognized.") from e

    def _get_permutation_matrix(self, permutation: List[int], num_qubits: int) -> np.ndarray:
        dim = 2**num_qubits; basis_indices = np.arange(dim)
        binary_basis = (((basis_indices[:, None] & (1 << np.arange(num_qubits - 1, -1, -1))) > 0)).astype(int)
        permuted_binary_basis = binary_basis[:, permutation]
        permuted_indices = (permuted_binary_basis * (1 << np.arange(num_qubits - 1, -1, -1))).sum(axis=1)
        P = np.zeros((dim, dim), dtype=int); P[permuted_indices, basis_indices] = 1; return P

    def _simulate_statevector(self, circuit: QuantumCircuit, apply_coherent_errors: bool) -> np.ndarray:
        num_qubits = len(circuit.qubits); qubit_to_pos = {qubit: i for i, qubit in enumerate(circuit.qubits)}
        state_vector = np.zeros(2**num_qubits, dtype=complex); state_vector[0] = 1.0
        
        for gate in circuit.gates:
            ideal_gate_matrix = self._get_ideal_gate_matrix(gate)
            gate_matrix_to_apply = ideal_gate_matrix
            num_gate_qubits = len(gate.qubits)

            if apply_coherent_errors:
                if num_gate_qubits == 1 and self.coherent_1q_error_angle != 0:
                    angle = self.coherent_1q_error_angle
                    error_matrix = np.array([[np.exp(-1j*angle/2), 0], [0, np.exp(1j*angle/2)]], dtype=complex)
                    gate_matrix_to_apply = error_matrix @ ideal_gate_matrix
                elif num_gate_qubits == 2 and self.coherent_2q_error_angle != 0:
                    angle = self.coherent_2q_error_angle
                    phase_neg = np.exp(-1j * angle / 2); phase_pos = np.exp(1j * angle / 2)
                    error_matrix = np.diag([phase_neg, phase_pos, phase_pos, phase_neg])
                    gate_matrix_to_apply = error_matrix @ ideal_gate_matrix
            
            target_pos = [qubit_to_pos[q] for q in gate.qubits]; other_pos = [i for i in range(num_qubits) if i not in target_pos]
            permutation = target_pos + other_pos; P = self._get_permutation_matrix(permutation, num_qubits)
            op_on_subspace = gate_matrix_to_apply; identity_part = np.eye(2**(num_qubits - num_gate_qubits))
            full_op = np.kron(op_on_subspace, identity_part); final_operator = P.T @ full_op @ P
            state_vector = final_operator @ state_vector
        return state_vector

    def _get_probabilities_from_statevector(self, state_vector: np.ndarray) -> Dict[str, float]:
        num_qubits = int(np.log2(len(state_vector))); probabilities = np.abs(state_vector)**2
        return {format(i, f'0{num_qubits}b'): prob for i, prob in enumerate(probabilities)}

    def _sample_from_probabilities(self, probabilities: Dict[str, float], shots: int) -> Dict[str, int]:
        if not probabilities: return {}
        bitstrings, probs = list(probabilities.keys()), list(probabilities.values())
        probs_sum = np.sum(probs)
        if not np.isclose(probs_sum, 1.0) and probs_sum > 0:
            probs = np.array(probs) / probs_sum
        elif probs_sum == 0: # Handle case of all-zero probabilities
            return {b: 0 for b in bitstrings}
        samples = np.random.choice(bitstrings, size=shots, p=probs)
        counts = dict(zip(*np.unique(samples, return_counts=True)))
        # Ensure all bitstrings are in the final counts dictionary
        final_counts = {b: 0 for b in bitstrings}
        final_counts.update(counts)
        return final_counts

    def run(self, circuit: QuantumCircuit, shots: int) -> Tuple[Dict[str, float], Dict[str, int]]:
        num_qubits = len(circuit.qubits); d = 2**num_qubits

        ideal_statevector = self._simulate_statevector(circuit, apply_coherent_errors=False)
        ideal_probabilities = self._get_probabilities_from_statevector(ideal_statevector)

        statevector_after_coherent = self._simulate_statevector(circuit, apply_coherent_errors=True)
        probs_after_coherent = self._get_probabilities_from_statevector(statevector_after_coherent)
        
        num_1q_gates = sum(1 for g in circuit.gates if len(g.qubits) == 1 and g.name.lower() != 'measure')
        num_2q_gates = sum(1 for g in circuit.gates if len(g.qubits) == 2)
        
        total_fidelity = ( (1.0 - self.depolarizing_error_1q) ** num_1q_gates * 
                           (1.0 - self.depolarizing_error_2q) ** num_2q_gates )
        total_effective_error = 1.0 - total_fidelity
        
        probs_after_depolarizing = {}
        if total_effective_error > 1e-15:
            uniform_prob = total_effective_error / d
            for bitstring, prob in probs_after_coherent.items():
                probs_after_depolarizing[bitstring] = (1 - total_effective_error) * prob + uniform_prob
        else:
            probs_after_depolarizing = probs_after_coherent

        final_noisy_probabilities = {}
        e = self.spam_error
        if e > 1e-15:
            M_1q = np.array([[1 - e, e], [e, 1 - e]]); M_total = M_1q
            for _ in range(num_qubits - 1): M_total = np.kron(M_total, M_1q)
            prob_vector = np.array([probs_after_depolarizing.get(format(i, f'0{num_qubits}b'), 0.0) for i in range(d)])
            observed_prob_vector = M_total @ prob_vector
            final_noisy_probabilities = {format(i, f'0{num_qubits}b'): p for i, p in enumerate(observed_prob_vector)}
        else:
            final_noisy_probabilities = probs_after_depolarizing

        noisy_counts = self._sample_from_probabilities(final_noisy_probabilities, shots)
        
        return ideal_probabilities, noisy_counts