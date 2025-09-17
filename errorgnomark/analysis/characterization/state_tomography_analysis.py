# File Path: errorgnomark/analysis/characterization/state_tomography_analysis.py
# FINAL CORRECTED VERSION - Implements the full optimization model from Equation (4)
# including c1 and c2 regularization terms, while maintaining full API compatibility.

import numpy as np
import itertools
from typing import List, Dict, Any, Optional

from errorgnomark.analysis.analysis_results import AnalysisResult

class StateTomographyAnalysis:
    """
    A comprehensive analysis tool for state tomography experiments.
    This version is fully compatible with previous calling conventions.
    """

    def __init__(self, qubits: List[int]):
        """Initializes the analysis tool for a given set of qubits."""
        self.qubits = qubits
        self.num_qubits = len(qubits)
        self.dim = 2**self.num_qubits
        self._pauli_basis_matrices = self._get_pauli_basis_matrices()

    # =========================================================================
    # --- METHOD 1: Flexible Analysis (Full Tomography & DFE) ---
    # This method's structure is preserved for full backward compatibility.
    # =========================================================================
    def analyze(self, experiment_data: Dict[str, Any], **kwargs: Any) -> AnalysisResult:
        """
        Performs analysis based on the provided arguments. The public interface
        and behavior of this method are unchanged to ensure compatibility.
        """
        ideal_density_matrix = kwargs.get('ideal_density_matrix')
        target_state_vector = kwargs.get('target_state_vector')

        # Case 1: Full Tomography
        if ideal_density_matrix is not None:
            print("\nAnalyzing results using Full Tomography (Linear Inversion)...")
            rho_physical = self._reconstruct_rho_linear_inversion(experiment_data)
            fidelity = self._calculate_fidelity(rho_physical, ideal_density_matrix)
            purity = np.real(np.trace(rho_physical @ rho_physical))
            trace = np.real(np.trace(rho_physical))

            return AnalysisResult(
                analysis_type="Full Tomography",
                method="Linear Inversion",
                reconstructed_rho=rho_physical,
                fidelity_with_ideal=fidelity,
                purity=purity,
                trace=trace
            )

        # Case 2: Direct Fidelity Estimation (Compatible Version)
        elif target_state_vector is not None:
            print("\nAnalyzing results using Direct Fidelity Estimation (DFE)...")
            fidelity = self._direct_fidelity_estimation(experiment_data, target_state_vector)
            rho_physical = self._reconstruct_rho_linear_inversion(experiment_data)
            purity = np.real(np.trace(rho_physical @ rho_physical))
            trace = np.real(np.trace(rho_physical))

            return AnalysisResult(
                analysis_type="Direct Fidelity Estimation",
                method="DFE from Pauli Expectation Values",
                reconstructed_rho=rho_physical,
                fidelity_with_ideal=fidelity,
                purity=purity,
                trace=trace
            )

        # Case 3: Reconstruction only
        else:
            print("\nAnalyzing results using Reconstruction Only (Linear Inversion)...")
            rho_physical = self._reconstruct_rho_linear_inversion(experiment_data)
            purity = np.real(np.trace(rho_physical @ rho_physical))
            trace = np.real(np.trace(rho_physical))

            return AnalysisResult(
                analysis_type="Reconstruction Only",
                method="Linear Inversion",
                reconstructed_rho=rho_physical,
                fidelity_with_ideal=None,
                purity=purity,
                trace=trace
            )

    # =========================================================================
    # --- METHOD 2: Nesterov Optimization (with Full Model Implementation) ---
    # =========================================================================
    def analyze_with_nesterov(self, experiment_data: Dict[str, Any], **kwargs: Any) -> AnalysisResult:
        """
        Analyzes tomography data using Nesterov's accelerated gradient descent,
        now fully implementing the model from Equation (4).
        """
        # --- [MODIFICATION 1] ---
        # Get all parameters from kwargs for full compatibility.
        max_iter = kwargs.get('max_iter', 500)
        learning_rate = kwargs.get('learning_rate', 0.01)
        tolerance = kwargs.get('tolerance', 1e-8)
        c1 = kwargs.get('c1', 0.01)  # Purity regularization term
        c2 = kwargs.get('c2', 0.03)  # Trace regularization term
        target_state = kwargs.get('target_state') # For fidelity calculation
        
        measured_bases_names = [k for k in experiment_data.keys() if k != 'num_qubits']
        if not measured_bases_names:
            raise ValueError("Experiment data contains no measurement bases.")

        measured_exp_vals = np.array([experiment_data[b]['expectation'] for b in measured_bases_names])
        measured_ops_tensor = np.array([self._pauli_string_to_matrix(b) for b in measured_bases_names])

        rho_k = np.eye(self.dim, dtype=complex) / self.dim
        y_k = rho_k.copy()
        t_k = 1.0

        print(f"Starting Nesterov optimization (max_iter={max_iter}, lr={learning_rate}, tol={tolerance}, c1={c1}, c2={c2})...")
        i = 0
        for i in range(max_iter):
            rho_prev = rho_k.copy()
            
            predicted_exp_vals = np.real(np.einsum('aij,ji->a', measured_ops_tensor, y_k))
            errors = predicted_exp_vals - measured_exp_vals
            
            # --- [MODIFICATION 2] ---
            # Calculate the full gradient according to Equation (4).
            # 1. Least-squares term gradient
            gradient = np.tensordot(errors, measured_ops_tensor, axes=1)
            
            # 2. Add gradient from c1 regularization term (purity)
            if c1 != 0:
                # The factor of 0.5 in the formula's least-squares term is cancelled by the derivative's factor of 2.
                # The derivative of c1 * Tr(rho^2) is 2 * c1 * rho.
                gradient += 2 * c1 * y_k
            
            # 3. Add gradient from c2 regularization term (trace)
            if c2 != 0:
                # The derivative of c2 * Tr(rho) is c2 * I.
                gradient += c2 * np.eye(self.dim, dtype=complex)

            # Nesterov update steps
            rho_k_next_unproj = y_k - learning_rate * gradient
            rho_k_next = self._project_to_physical(rho_k_next_unproj)
            t_k_next = (1 + np.sqrt(1 + 4 * t_k**2)) / 2
            y_k_next = rho_k_next + ((t_k - 1) / t_k_next) * (rho_k_next - rho_k)
            rho_k, y_k, t_k = rho_k_next, y_k_next, t_k_next
            
            change = np.linalg.norm(rho_k - rho_prev, 'fro')
            if (i + 1) % 100 == 0:
                print(f"  Iter {i+1}: Change = {change:.4e}")
            if change < tolerance:
                print(f"Convergence reached at iteration {i+1}.")
                break
        else:
            print("Warning: Maximum iterations reached without convergence.")
            
        rho_physical = rho_k
        fidelity = self._calculate_fidelity(rho_physical, target_state)
        purity = np.real(np.trace(rho_physical @ rho_physical))
        trace = np.real(np.trace(rho_physical))

        return AnalysisResult(
            analysis_type="Efficient Tomography",
            method=f"Nesterov Optimization ({i+1} iter)",
            reconstructed_rho=rho_physical,
            fidelity_with_ideal=fidelity,
            purity=purity,
            trace=trace
        )

    # =========================================================================
    # --- Helper Methods (Unchanged) ---
    # =========================================================================
    def _reconstruct_rho_linear_inversion(self, experiment_data: Dict[str, Any]) -> np.ndarray:
        measured_bases = [k for k in experiment_data.keys() if k != 'num_qubits']
        exp_vals_vec = np.array([experiment_data[basis]['expectation'] for basis in measured_bases])
        measurement_matrix = self._build_measurement_matrix(measured_bases)
        coeffs = np.linalg.pinv(measurement_matrix) @ exp_vals_vec
        rho_reconstructed = sum(c * G for c, G in zip(coeffs, self._pauli_basis_matrices.values()))
        return self._project_to_physical(rho_reconstructed)

    def _direct_fidelity_estimation(self, experiment_data: Dict[str, Any], target_state_vector: np.ndarray) -> float:
        fidelity = 0.0
        bases = [k for k in experiment_data.keys() if k != 'num_qubits']
        target_state_vector = target_state_vector.reshape(-1, 1)

        for basis_str in bases:
            measured_expectation = experiment_data[basis_str].get('expectation', 0.0)
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
        if target is None:
            return None
        if target.ndim == 1:
            target = np.outer(target, target.conj())
        
        sqrt_rho = self._matrix_sqrt(rho)
        val = self._matrix_sqrt(sqrt_rho @ target @ sqrt_rho)
        fidelity = np.real(np.trace(val))**2
        return max(0.0, min(1.0, fidelity))

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
        if len(pauli_string) != self.num_qubits:
            pauli_string = pauli_string.ljust(self.num_qubits, 'I')
        mat = np.array([[1.0]], dtype=complex)
        for char in pauli_string:
            mat = np.kron(mat, self._get_pauli(char))
        return mat

    def _get_pauli_basis_matrices(self) -> Dict[str, np.ndarray]:
        paulis = ['I', 'X', 'Y', 'Z']
        basis_matrices = {}
        for pauli_tuple in itertools.product(paulis, repeat=self.num_qubits):
            pauli_string = "".join(pauli_tuple)
            basis_matrices[pauli_string] = self._pauli_string_to_matrix(pauli_string)
        return basis_matrices