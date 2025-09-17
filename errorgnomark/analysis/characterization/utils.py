# File Path: errorgnomark/analysis/characterization/utils.py
# This is the consolidated and corrected utilities file.

import numpy as np
import itertools
from typing import Dict, List
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# --- [KEPT FROM YOUR ORIGINAL FILE] ---
# This dictionary is the single source of truth for single-qubit Pauli matrices.
_SINGLE_QUBIT_PAULIS = {
    'I': np.array([[1, 0], [0, 1]], dtype=complex),
    'X': np.array([[0, 1], [1, 0]], dtype=complex),
    'Y': np.array([[0, -1j], [1j, 0]], dtype=complex),
    'Z': np.array([[1, 0], [0, -1]], dtype=complex),
}

# --- [KEPT AND ENHANCED FROM YOUR ORIGINAL FILE] ---
def get_pauli_basis_matrices(num_qubits: int, skip_identity: bool = False) -> Dict[str, np.ndarray]:
    """
    Generates the full N-qubit Pauli basis matrices.

    Args:
        num_qubits: The number of qubits.
        skip_identity: If True, skips the all-identity matrix 'I...I'.

    Returns:
        A dictionary mapping Pauli strings (e.g., 'IX', 'ZY') to their
        corresponding matrix representations.
    """
    if num_qubits <= 0:
        return {}

    basis = {}
    pauli_strings = itertools.product('IXYZ', repeat=num_qubits)
    identity_label = 'I' * num_qubits

    for pauli_tuple in pauli_strings:
        label = "".join(pauli_tuple)
        if skip_identity and label == identity_label:
            continue
        
        mat = np.array([[1.0]], dtype=complex)
        for p_char in pauli_tuple:
            mat = np.kron(mat, _SINGLE_QUBIT_PAULIS[p_char])
        basis[label] = mat
        
    return basis

# --- [NEWLY ADDED TO FIX THE IMPORT ERROR] ---
def get_ideal_state(label: str, qubits: List[int]) -> np.ndarray:
    """
    Generates the ideal density matrix for a given named state.
    """
    label = label.lower()
    num_qubits = len(qubits)
    
    if label == 'bell':
        if num_qubits != 2:
            raise ValueError("Bell state is a 2-qubit state.")
        psi = (1 / np.sqrt(2)) * np.array([1, 0, 0, 1], dtype=complex)
    else:
        raise ValueError(f"Unknown ideal state label: '{label}'")

    return np.outer(psi, psi.conj())

# --- [NEWLY ADDED TO FIX THE IMPORT ERROR] ---
def plot_density_matrix(rho: np.ndarray, path: str, title: str = "Density Matrix"):
    """
    Generates and saves a 3D bar plot of a density matrix.
    """
    dim = rho.shape[0]
    x_labels = [f"|{i:0{int(np.log2(dim))}b}⟩" for i in range(dim)]
    y_labels = [f"⟨{i:0{int(np.log2(dim))}b}|" for i in range(dim)]
    
    fig = plt.figure(figsize=(12, 5))
    fig.suptitle(title, fontsize=16)

    # Plot Real Part
    ax1 = fig.add_subplot(121, projection='3d')
    xpos, ypos = np.meshgrid(np.arange(dim), np.arange(dim))
    xpos, ypos = xpos.flatten(), ypos.flatten()
    zpos = np.zeros_like(xpos)
    dx = dy = 0.8 * np.ones_like(zpos)
    dz_real = np.real(rho).flatten()
    
    max_height = np.max(np.abs(rho)) if np.max(np.abs(rho)) > 0 else 1.0
    
    ax1.bar3d(xpos, ypos, zpos, dx, dy, dz_real, color='skyblue')
    ax1.set_title('Real Part')
    ax1.set_xticks(np.arange(dim))
    ax1.set_yticks(np.arange(dim))
    ax1.set_xticklabels(x_labels, rotation=45)
    ax1.set_yticklabels(y_labels, rotation=-45)
    ax1.set_zlim(-max_height, max_height)
    ax1.set_zlabel('Amplitude')

    # Plot Imaginary Part
    ax2 = fig.add_subplot(122, projection='3d')
    dz_imag = np.imag(rho).flatten()
    
    ax2.bar3d(xpos, ypos, zpos, dx, dy, dz_imag, color='salmon')
    ax2.set_title('Imaginary Part')
    ax2.set_xticks(np.arange(dim))
    ax2.set_yticks(np.arange(dim))
    ax2.set_xticklabels(x_labels, rotation=45)
    ax2.set_yticklabels(y_labels, rotation=-45)
    ax2.set_zlim(-max_height, max_height)
    ax2.set_zlabel('Amplitude')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(path)
    plt.close(fig)