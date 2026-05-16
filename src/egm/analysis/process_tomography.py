# File Path: errorgnomark/analysis/process_tomography.py

# ==============================================================
# Quantum Process Tomography (QPT) Analysis Module [FINAL v5.1]
# --------------------------------------------------------------
# This module provides a class for performing Quantum Process Tomography (QPT)
# analysis based on experimental counts from Pauli basis measurements.
#
# It retains the exact logic and interfaces of version 5, with enhancements
# focused on code structure, readability, and documentation.
#
# Compatible with Experiment v4 (Pauli basis = {I, X, Y, Z})
# Provides:
#   • Linear inversion from raw counts (χ matrix)
#   • MLE-style physical projection (Hermitian + PSD + Tr = d)
#   • χ → Choi conversion for fidelity & visualization
# ==============================================================

from functools import reduce
from itertools import product
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np

from egm.analysis.result import ExperimentResult

# --- Module-Level Constants and Type Definitions ---

# Define the single-qubit Pauli matrices as a constant for reuse.
PAULI_MATRICES = {
    'I': np.array([[1, 0], [0, 1]], dtype=complex),
    'X': np.array([[0, 1], [1, 0]], dtype=complex),
    'Y': np.array([[0, -1j], [1j, 0]], dtype=complex),
    'Z': np.array([[1, 0], [0, -1]], dtype=complex),
}

# Type alias for raw experimental data structure.
RawCountsData = Dict[str, Dict[str, Dict[str, int]]]


# ==============================================================
# Utility: Representation Conversions
# ==============================================================

def _get_pauli_basis(num_qubits: int, normalize: bool) -> List[np.ndarray]:
    """
    Internal helper to generate the multi-qubit Pauli basis operators.

    Args:
        num_qubits: The number of qubits.
        normalize: If True, normalizes operators such that Tr(P_i† P_j) = d * δ_ij.

    Returns:
        A list of (d, d) Pauli basis operators.
    """
    dim = 2 ** num_qubits
    pauli_labels = product('IXYZ', repeat=num_qubits)
    
    basis_ops = [reduce(np.kron, [PAULI_MATRICES[p] for p in label]) for label in pauli_labels]
        
    if normalize:
        norm_factor = 1 / np.sqrt(dim)
        return [op * norm_factor for op in basis_ops]
    
    return basis_ops


def chi_to_choi(chi: np.ndarray, num_qubits: int) -> np.ndarray:
    """
    Convert χ (Pauli-basis) to Choi matrix (J) in Hilbert–Schmidt representation.

    Args:
        chi: The (N, N) chi matrix, where N = 4**num_qubits.
        num_qubits: The number of qubits.

    Returns:
        The (d**2, d**2) Choi matrix, where d = 2**num_qubits.
    """
    dim = 2 ** num_qubits
    pauli_basis_ops = _get_pauli_basis(num_qubits, normalize=True)

    J = np.zeros((dim ** 2, dim ** 2), dtype=complex)
    for m, E_m in enumerate(pauli_basis_ops):
        for n, E_n in enumerate(pauli_basis_ops):
            # The formula is J(E) = sum_{m,n} χ_mn * |E_m>> <<E_n|
            # which is equivalent to the tensor product construction below.
            # Note: The original code used E_n.conj(), which is equivalent to E_n.T
            # for Pauli operators. We keep this for logical consistency.
            J += chi[m, n] * np.kron(E_m, E_n.conj())
    return J


# ==============================================================
# Main Analysis Class
# ==============================================================

class ProcessTomographyAnalysis:
    """
    Enhanced QPT analysis (Pauli basis {I, X, Y, Z}).
    
    This class encapsulates the QPT workflow, from reconstructing the
    process matrix from raw counts to calculating fidelity. The internal
    logic is identical to v5.
    """

    def __init__(self, qubits: List[int]):
        """
        Initializes the QPT analyzer for a specific set of qubits.

        Args:
            qubits: A list of qubit indices being analyzed.
        """
        self.qubits = qubits
        self.num_qubits = len(qubits)
        self.dim = 2 ** self.num_qubits
        self.pauli_basis = ['I', 'X', 'Y', 'Z'] # Maintained for compatibility

    def analyze(self, raw_counts_data: RawCountsData, ideal_choi: Optional[np.ndarray] = None) -> ExperimentResult:
        """
        Executes the full QPT analysis pipeline.

        Args:
            raw_counts_data: A nested dictionary with the structure:
                             {prep_label: {meas_label: {bitstring: counts}}}.
            ideal_choi: The ideal Choi matrix of the target process. If provided,
                        process fidelity will be calculated.

        Returns:
            An ExperimentResult object containing the analysis results.
        """
        print("[INFO] Starting Process Tomography Analysis [v5]")
        chi_matrix = self._reconstruct_chi(raw_counts_data)
        choi_matrix = chi_to_choi(chi_matrix, self.num_qubits)

        fidelity = None
        if ideal_choi is not None:
            d = self.dim
            # The fidelity calculation is preserved exactly as in the original code.
            # F = Re[Tr(J_recon† * J_ideal)] / d²
            overlap = np.trace(choi_matrix.conj().T @ ideal_choi)
            fid = np.real(overlap / (d ** 2))
            fidelity = np.clip(fid, 0.0, 1.0)
            print(f"[INFO] Process Fidelity = {fidelity:.4f}")

        return ExperimentResult(
            name="ProcessFidelity",
            data={
                "reconstructed_chi": chi_matrix,
                "reconstructed_choi": choi_matrix,
                "process_fidelity": fidelity,
            },
        )

    def _reconstruct_chi(self, raw_counts_data: RawCountsData) -> np.ndarray:
        """
        Performs linear inversion + physical projection to get the χ matrix.
        This method's logic is identical to the original v5 implementation.
        """
        num_qubits = self.num_qubits
        dim = self.dim
        num_basis = 4 ** num_qubits

        # --- Normalized Pauli operator basis ---
        pauli_basis = np.array(_get_pauli_basis(num_qubits, normalize=True))

        # --- State preparation helper ---
        def prep_state(label: str) -> np.ndarray:
            states = []
            for ch in label:
                if ch == 'X':    # |+⟩⟨+|
                    states.append(np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex))
                elif ch == 'Y':  # |+i⟩⟨+i|
                    states.append(np.array([[0.5, -0.5j], [0.5j, 0.5]], dtype=complex))
                else:            # |0⟩⟨0| for Z/I basis
                    states.append(np.array([[1, 0], [0, 0]], dtype=complex))
            # Use reduce for a robust Kronecker product over the list of states.
            return reduce(np.kron, states)

        # --- Measurement operator helper ---
        def meas_op(label: str) -> List[np.ndarray]:
            ops_per_qubit = []
            for ch in label:
                if ch == 'X':    # X basis projectors
                    proj0 = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
                    proj1 = np.array([[0.5, -0.5], [-0.5, 0.5]], dtype=complex)
                elif ch == 'Y':  # Y basis projectors
                    proj0 = np.array([[0.5, -0.5j], [0.5j, 0.5]], dtype=complex)
                    proj1 = np.array([[0.5, 0.5j], [-0.5j, 0.5]], dtype=complex)
                else:            # Z basis projectors
                    proj0 = np.array([[1, 0], [0, 0]], dtype=complex)
                    proj1 = np.array([[0, 0], [0, 1]], dtype=complex)
                ops_per_qubit.append((proj0, proj1))
            
            proj_list = []
            # Generate 2^n multi-qubit projectors from single-qubit projectors
            for bits in product([0, 1], repeat=num_qubits):
                projector = reduce(np.kron, [ops_per_qubit[i][b] for i, b in enumerate(bits)])
                proj_list.append(projector)
            return proj_list

        # --- Build linear system A·χ = y ---
        A_rows, y_vec = [], []
        for prep_label, meas_dict in raw_counts_data.items():
            rho_in = prep_state(prep_label)
            for meas_label, counts in meas_dict.items():
                total = sum(counts.values())
                if total == 0:
                    continue
                projs = meas_op(meas_label)
                for bit, c in counts.items():
                    prob = c / total
                    # The original modulo logic is preserved.
                    idx = int(bit, 2) % len(projs)
                    M = projs[idx]
                    # Coefficient for χ_mn is Tr[M * E_m * ρ_in * E_n^†]
                    row = [
                        np.trace(M @ (pauli_basis[m] @ rho_in @ pauli_basis[n].conj().T))
                        for m in range(num_basis)
                        for n in range(num_basis)
                    ]
                    A_rows.append(row)
                    y_vec.append(prob)

        A = np.array(A_rows, dtype=complex)
        y = np.array(y_vec, dtype=complex)
        print(f"[DEBUG] Linear system: {A.shape[0]} eqs × {A.shape[1]} unknowns")

        # --- Least-squares + physical (MLE-like) projection ---
        # The sequence of operations is preserved exactly from the original.
        chi_vec, *_ = np.linalg.lstsq(A, y, rcond=None)
        chi = chi_vec.reshape((num_basis, num_basis))
        
        # 1. Enforce Hermiticity
        chi = 0.5 * (chi + chi.conj().T)

        # 2. Enforce Trace-Preserving condition (first pass)
        tr = np.trace(chi)
        if abs(tr) > 1e-12:
            chi *= dim / tr

        # 3. Enforce Positivity
        vals, vecs = np.linalg.eigh(chi)
        vals = np.clip(vals.real, 0, None)
        chi_phys = vecs @ np.diag(vals) @ vecs.conj().T
        
        # 4. Re-enforce Hermiticity and Trace-Preserving condition (final)
        chi_phys = 0.5 * (chi_phys + chi_phys.conj().T)
        chi_phys *= dim / np.trace(chi_phys)

        print(f"[INFO] χ matrix reconstructed: shape={chi_phys.shape}, Tr={np.trace(chi_phys):.3f}")
        return chi_phys


# ==============================================================
# Visualization: Pauli Transfer Matrix (PTM)
# ==============================================================

def choi_to_pauli_transfer_matrix(choi: np.ndarray, num_qubits: int) -> np.ndarray:
    """
    Converts a Choi matrix (J) to a Pauli Transfer Matrix (PTM).
    
    The PTM describes how the expectation values of Pauli operators evolve.
    Note: The original code's logic, including the use of normalized Pauli
    operators, is preserved for consistency.
    """
    dim = 2 ** num_qubits
    num_basis = 4 ** num_qubits
    
    # The original implementation used normalized Paulis. We preserve this.
    paulis = _get_pauli_basis(num_qubits, normalize=True)

    # Reshape Choi matrix to superoperator S that acts on vectorized density matrices
    S = choi.reshape(dim, dim, dim, dim).transpose(0, 2, 1, 3).reshape(dim ** 2, dim ** 2)
    
    PTM = np.zeros((num_basis, num_basis), dtype=float)
    for m, Pm in enumerate(paulis):
        for n, Pn in enumerate(paulis):
            # Vectorize input Pauli Pn (column-major 'F' order)
            vec = Pn.flatten('F')
            # Apply channel superoperator: |E(Pn)>> = S |Pn>>
            out_vec = S @ vec
            # Reshape back to a matrix E(Pn)
            out_mat = out_vec.reshape(dim, dim, order='F')
            # PTM_mn = (1/d) * Tr(Pm^† * E(Pn))
            PTM[m, n] = np.real(np.trace(Pm.conj().T @ out_mat)) / dim
            
    return PTM


def compare_pauli_transfer_matrices(choi_true: np.ndarray, choi_est: np.ndarray, num_qubits: int):
    """
    Visualizes a side-by-side comparison of the ideal and estimated PTMs.
    """
    ptm_true = choi_to_pauli_transfer_matrix(choi_true, num_qubits)
    ptm_est = choi_to_pauli_transfer_matrix(choi_est, num_qubits)
    labels = [''.join(p) for p in product(['I', 'X', 'Y', 'Z'], repeat=num_qubits)]

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    plt.style.use('seaborn-v0_8-whitegrid')

    plot_data = [
        ("Ideal", ptm_true),
        ("Estimate", ptm_est)
    ]
    
    # Use a diverging colormap centered at 0
    cmap = "RdBu_r"
    norm = plt.Normalize(-1, 1)

    for i, (title, matrix) in enumerate(plot_data):
        ax = axes[i]
        im = ax.imshow(matrix, cmap=cmap, norm=norm)
        ax.set_title(title, fontsize=14)
        ax.set_xticks(np.arange(len(labels)))
        ax.set_xticklabels(labels, rotation=90, fontsize=9)
        ax.set_yticks(np.arange(len(labels)))
        ax.set_yticklabels(labels, fontsize=9)
        
        # Draw grid lines
        ax.set_xticks(np.arange(-.5, len(labels), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(labels), 1), minor=True)
        ax.grid(which="minor", color="grey", linestyle='-', linewidth=0.5)
        ax.tick_params(which="minor", size=0)

    fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.046, pad=0.04, label="Matrix Element Value")
    fig.suptitle("Pauli Transfer Matrix Comparison", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()