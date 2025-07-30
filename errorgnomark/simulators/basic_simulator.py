# errorgnomark/simulators/basic_simulator.py
import numpy as np
from typing import Dict, List
from errorgnomark.circuits.circuit import QuantumCircuit

# Define matrices for single-qubit gates
# We use numpy for complex number calculations
GATE_MATRICES: Dict[str, np.ndarray] = {
    'h': 1/np.sqrt(2) * np.array([[1,  1], [1, -1]]),
    's': np.array([[1, 0], [0, 1j]]),
    'x': np.array([[0, 1], [1, 0]]),
    'y': np.array([[0, -1j], [1j, 0]]),
    'z': np.array([[1, 0], [0, -1]]),
    'i': np.identity(2) # Identity matrix
}

def _rx_matrix(theta: float) -> np.ndarray:
    return np.array([
        [np.cos(theta / 2), -1j * np.sin(theta / 2)],
        [-1j * np.sin(theta / 2), np.cos(theta / 2)]
    ])

def _ry_matrix(theta: float) -> np.ndarray:
    return np.array([
        [np.cos(theta / 2), -np.sin(theta / 2)],
        [np.sin(theta / 2), np.cos(theta / 2)]
    ])

class BasicSimulator:
    """
    A basic single-qubit simulator that uses density matrices to support noise simulation.
    """
    def _get_gate_matrix(self, gate_name: str, params: List[float]) -> np.ndarray:
        """Gets the matrix representation of a gate based on its name and parameters."""
        if gate_name in GATE_MATRICES:
            return GATE_MATRICES[gate_name]
        elif gate_name == 'rx':
            return _rx_matrix(params[0])
        elif gate_name == 'ry':
            return _ry_matrix(params[0])
        else:
            raise ValueError(f"Gate '{gate_name}' is not supported by this basic simulator.")

    def _apply_depolarizing_noise(self, rho: np.ndarray, p: float) -> np.ndarray:
        """
        Applies the single-qubit depolarizing noise channel.
        rho_noisy = (1 - p) * rho + p * I/2
        """
        identity = np.identity(2)
        return (1 - p) * rho + p * identity / 2

    def _run(self, circuit: QuantumCircuit, noise_prob: float = 0.0) -> np.ndarray:
        """
        The core logic for running the circuit.
        """
        # Initial state is |0>, its density matrix is [[1, 0], [0, 0]]
        rho = np.zeros((2, 2), dtype=np.complex128)
        rho[0, 0] = 1

        # Apply each gate sequentially
        for gate in circuit.gates:
            # Get the gate matrix
            U = self._get_gate_matrix(gate.name, gate.params)
            # Apply the gate: rho -> U * rho * U_dagger
            rho = U @ rho @ U.conj().T
            
            # If noise is present, apply it after each gate
            if noise_prob > 0:
                rho = self._apply_depolarizing_noise(rho, noise_prob)
        
        return rho

    def simulate(self, circuit: QuantumCircuit) -> np.ndarray:
        """
        Performs an ideal, noiseless simulation.
        Returns the probabilities of measuring |0> and |1>.
        """
        final_rho = self._run(circuit, noise_prob=0.0)
        # Probabilities are the diagonal elements of the density matrix
        return np.real(final_rho.diagonal())

    def simulate_noisy(self, circuit: QuantumCircuit, depolarizing_prob: float) -> np.ndarray:
        """
        Performs a noisy simulation.
        Returns the probabilities of measuring |0> and |1>.
        """
        if not (0 <= depolarizing_prob <= 1):
            raise ValueError("Depolarizing probability must be between 0 and 1.")
        final_rho = self._run(circuit, noise_prob=depolarizing_prob)
        return np.real(final_rho.diagonal())