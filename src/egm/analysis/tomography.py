# File Path: errorgnomark/analysis/tomography.py
# [CORRECTED VERSION - Adapts to the existing ExperimentResult class]

import itertools
from typing import Any, Dict, List, Optional

import numpy as np

# =========================================================================
# [THE FIX IS HERE]
# Import the correct class name 'ExperimentResult' from your 'result.py' file.
from .result import ExperimentResult

# =========================================================================

class StateTomographyAnalysis:
    """
    A comprehensive analysis tool for state tomography experiments.
    This version is adapted to use the framework's standard ExperimentResult class.
    """
    def __init__(self, qubits: List[int]):
        self.qubits = qubits
        self.num_qubits = len(qubits)
        self.dim = 2**self.num_qubits
        self._pauli_basis_matrices = self._get_pauli_basis_matrices()

    def analyze_linear_inversion(self, experiment_data: Dict[str, Any], ideal_rho: Optional[np.ndarray] = None) -> ExperimentResult:
        print("\nAnalyzing results using Full Tomography (Linear Inversion)...")
        rho_physical = self._reconstruct_rho_linear_inversion(experiment_data)
        
        # [REFACTOR] Package results into the 'data' dictionary for ExperimentResult
        analysis_data = {
            'reconstructed_rho': rho_physical,
            'fidelity_with_ideal': self._calculate_fidelity(rho_physical, ideal_rho),
            'purity': np.real(np.trace(rho_physical @ rho_physical)),
            'trace': np.real(np.trace(rho_physical))
        }
        return ExperimentResult(name="Full Tomography (Linear Inversion)", data=analysis_data)

    def analyze_dfe(self, experiment_data: Dict[str, Any], ideal_statevector: np.ndarray) -> ExperimentResult:
        print("\nAnalyzing results using Direct Fidelity Estimation (DFE)...")
        rho_physical = self._reconstruct_rho_linear_inversion(experiment_data)

        # [REFACTOR] Package results into the 'data' dictionary for ExperimentResult
        analysis_data = {
            'reconstructed_rho': rho_physical,
            'fidelity_with_ideal': self._direct_fidelity_estimation(experiment_data, ideal_statevector),
            'purity': np.real(np.trace(rho_physical @ rho_physical)),
            'trace': np.real(np.trace(rho_physical))
        }
        return ExperimentResult(name="Direct Fidelity Estimation", data=analysis_data)

    def analyze_with_nesterov(self, experiment_data: Dict[str, Any], **kwargs: Any) -> ExperimentResult:
        max_iter = kwargs.get('max_iter', 500)
        learning_rate = kwargs.get('learning_rate', 0.01)
        tolerance = kwargs.get('tolerance', 1e-8)
        c1 = kwargs.get('c1', 0.01)
        c2 = kwargs.get('c2', 0.03)
        ideal_rho = kwargs.get('ideal_rho')
        
        measured_bases_names = list(experiment_data.keys())
        measured_exp_vals = np.array([experiment_data[b]['expectation'] for b in measured_bases_names])
        measured_ops_tensor = np.array([self._pauli_string_to_matrix(b) for b in measured_bases_names])

        rho_k = np.eye(self.dim, dtype=complex) / self.dim
        y_k, t_k = rho_k.copy(), 1.0

        print(f"Starting Nesterov optimization (max_iter={max_iter}, lr={learning_rate}, tol={tolerance}, c1={c1}, c2={c2})...")
        i = 0
        for i in range(max_iter):
            rho_prev = rho_k.copy()
            predicted_exp_vals = np.real(np.einsum('aij,ji->a', measured_ops_tensor, y_k))
            errors = predicted_exp_vals - measured_exp_vals
            
            gradient = np.tensordot(errors, measured_ops_tensor, axes=1)
            if c1 != 0: gradient += 2 * c1 * y_k
            if c2 != 0: gradient += c2 * np.eye(self.dim, dtype=complex)

            rho_k_next_unproj = y_k - learning_rate * gradient
            rho_k_next = self._project_to_physical(rho_k_next_unproj)
            t_k_next = (1 + np.sqrt(1 + 4 * t_k**2)) / 2
            y_k_next = rho_k_next + ((t_k - 1) / t_k_next) * (rho_k_next - rho_k)
            rho_k, y_k, t_k = rho_k_next, y_k_next, t_k_next
            
            change = np.linalg.norm(rho_k - rho_prev, 'fro')
            if (i + 1) % 100 == 0: print(f"  Iter {i+1}: Change = {change:.4e}")
            if change < tolerance:
                print(f"Convergence reached at iteration {i+1}.")
                break
        else:
            print("Warning: Maximum iterations reached without convergence.")
            
        # [REFACTOR] Package results into the 'data' dictionary for ExperimentResult
        analysis_data = {
            'reconstructed_rho': rho_k,
            'fidelity_with_ideal': self._calculate_fidelity(rho_k, ideal_rho),
            'purity': np.real(np.trace(rho_k @ rho_k)),
            'trace': np.real(np.trace(rho_k)),
            'iterations': i + 1
        }
        return ExperimentResult(name="Nesterov Optimization", data=analysis_data)

    # --- Helper methods below are unchanged ---
    def _reconstruct_rho_linear_inversion(self, experiment_data: Dict[str, Any]) -> np.ndarray:
        measured_bases = list(experiment_data.keys())
        exp_vals_vec = np.array([experiment_data[basis]['expectation'] for basis in measured_bases])
        measurement_matrix = self._build_measurement_matrix(measured_bases)
        coeffs = np.linalg.pinv(measurement_matrix) @ exp_vals_vec
        rho_reconstructed = sum(c * G for c, G in zip(coeffs, self._pauli_basis_matrices.values()))
        return self._project_to_physical(rho_reconstructed)

    def _direct_fidelity_estimation(self, experiment_data: Dict[str, Any], target_state_vector: np.ndarray) -> float:
        fidelity = 0.0
        target_state_vector = target_state_vector.reshape(-1, 1)
        for basis_str, data in experiment_data.items():
            measured_expectation = data.get('expectation', 0.0)
            pauli_op = self._pauli_string_to_matrix(basis_str)
            ideal_expectation = (target_state_vector.conj().T @ pauli_op @ target_state_vector)[0, 0].real
            fidelity += measured_expectation * ideal_expectation
        return max(0.0, min(1.0, fidelity / self.dim))

    def _build_measurement_matrix(self, measured_bases: List[str]) -> np.ndarray:
        num_measured = len(measured_bases)
        num_basis_ops = len(self._pauli_basis_matrices)
        measured_ops = [self._pauli_string_to_matrix(s) for s in measured_bases]
        basis_ops = list(self._pauli_basis_matrices.values())
        m_matrix = np.zeros((num_measured, num_basis_ops))
        for i in range(num_measured):
            for j in range(num_basis_ops):
                m_matrix[i, j] = np.real(np.trace(measured_ops[i] @ basis_ops[j]))
        return m_matrix

    def _project_to_physical(self, rho: np.ndarray) -> np.ndarray:
        rho = (rho + rho.conj().T) / 2
        eigvals, eigvecs = np.linalg.eigh(rho)
        eigvals[eigvals < 0] = 0
        trace = np.sum(eigvals)
        if trace > 1e-9:
            eigvals = eigvals / trace
        else:
            return np.eye(self.dim, dtype=complex) / self.dim
        return eigvecs @ np.diag(eigvals) @ eigvecs.conj().T

    def _calculate_fidelity(self, rho: np.ndarray, target: Optional[np.ndarray]) -> Optional[float]:
        if target is None: return None
        if target.ndim == 1: target = np.outer(target, target.conj())
        sqrt_rho = self._matrix_sqrt(rho)
        val = self._matrix_sqrt(sqrt_rho @ target @ sqrt_rho)
        return max(0.0, min(1.0, np.real(np.trace(val))**2))

    def _matrix_sqrt(self, mat: np.ndarray) -> np.ndarray:
        eigvals, eigvecs = np.linalg.eigh(mat)
        eigvals[eigvals < 0] = 0
        return eigvecs @ np.diag(np.sqrt(eigvals)) @ eigvecs.conj().T

    def _get_pauli(self, pauli_char: str) -> np.ndarray:
        if pauli_char == 'I': return np.array([[1, 0], [0, 1]], dtype=complex)
        if pauli_char == 'X': return np.array([[0, 1], [1, 0]], dtype=complex)
        if pauli_char == 'Y': return np.array([[0, -1j], [1j, 0]], dtype=complex)
        if pauli_char == 'Z': return np.array([[1, 0], [0, -1]], dtype=complex)
        raise ValueError(f"Invalid Pauli character '{pauli_char}'.")

    def _pauli_string_to_matrix(self, pauli_string: str) -> np.ndarray:
        mat = np.array([[1.0]], dtype=complex)
        for char in pauli_string:
            mat = np.kron(mat, self._get_pauli(char))
        return mat

    def _get_pauli_basis_matrices(self) -> Dict[str, np.ndarray]:
        return {
            "".join(p): self._pauli_string_to_matrix("".join(p))
            for p in itertools.product('IXYZ', repeat=self.num_qubits)
        }