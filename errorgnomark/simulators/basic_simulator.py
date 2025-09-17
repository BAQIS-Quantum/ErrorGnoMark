# errorgnomark/simulators/basic_simulator.py
import numpy as np
from typing import Dict, List, Optional
from collections import Counter

# We assume the QuantumCircuit definition is in this path.
from errorgnomark.circuits.circuit import QuantumCircuit

# --- 1. Modular Noise Model Definition ---
# This makes the simulator more extensible. We can add other models like
# AmplitudeDampingNoiseModel in the future.

class NoiseModel:
    """Base class for noise models to allow for type hinting."""
    pass

class DepolarizingNoiseModel(NoiseModel):
    """
    A simple noise model for single-qubit depolarizing error.
    """
    def __init__(self, probability: float):
        if not (0 <= probability <= 1):
            raise ValueError("Depolarizing probability must be between 0 and 1.")
        self.probability = probability

# --- 2. Gate Matrix Definitions (Unchanged) ---
GATE_MATRICES: Dict[str, np.ndarray] = {
    'h': 1/np.sqrt(2) * np.array([[1,  1], [1, -1]]),
    's': np.array([[1, 0], [0, 1j]]),
    'x': np.array([[0, 1], [1, 0]]),
    'y': np.array([[0, -1j], [1j, 0]]),
    'z': np.array([[1, 0], [0, -1]]),
    'i': np.identity(2)
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

# --- 3. Refactored Simulator Class ---

class BasicSimulator:
    """
    A basic single-qubit simulator that runs circuits for a given number of shots
    and returns measurement counts. It supports an optional noise model.
    """
    def run(
        self,
        circuit: QuantumCircuit,
        shots: int,
        noise_model: Optional[NoiseModel] = None
    ) -> Dict[str, int]:
        """
        Executes the quantum circuit and returns measurement outcomes.

        Args:
            circuit: The QuantumCircuit object to simulate.
            shots: The number of times to run the circuit and measure the outcome.
            noise_model: An optional noise model to apply after each gate.

        Returns:
            A dictionary with bitstring keys ('0', '1') and integer values
            representing the number of times each outcome was measured.
            Example: {'0': 505, '1': 495}
        """
        # Determine the noise probability from the provided model
        noise_prob = 0.0
        if isinstance(noise_model, DepolarizingNoiseModel):
            noise_prob = noise_model.probability
        elif noise_model is not None:
            # This allows us to add more noise models later
            raise TypeError("Unsupported noise model type.")

        # --- Step 1: Calculate the final state's probabilities ---
        # This part uses the density matrix evolution
        final_rho = self._evolve_state(circuit, noise_prob)
        # Probabilities are the diagonal elements of the final density matrix
        probabilities = np.real(final_rho.diagonal())
        
        # Ensure probabilities are clean for sampling
        probabilities /= np.sum(probabilities)

        # --- Step 2: Simulate 'shots' measurements based on the probabilities ---
        # The possible outcomes for a single qubit are 0 and 1
        outcomes = [0, 1]
        # Use numpy's random choice to sample 'shots' times
        measurement_results = np.random.choice(outcomes, size=shots, p=probabilities)

        # --- Step 3: Count the results and format the output dictionary ---
        counts = Counter(measurement_results)
        
        # Format the keys as strings ('0', '1') and ensure all outcomes are present
        final_counts = {
            '0': counts.get(0, 0),
            '1': counts.get(1, 0)
        }
        
        return final_counts

    def _evolve_state(self, circuit: QuantumCircuit, noise_prob: float) -> np.ndarray:
        """
        Internal logic to evolve the density matrix through the circuit.
        This is the core of the simulation.
        """
        # Initial state is |0>, its density matrix is [[1, 0], [0, 0]]
        rho = np.zeros((2, 2), dtype=np.complex128)
        rho[0, 0] = 1

        # Apply each gate sequentially
        for gate in circuit.gates:
            U = self._get_gate_matrix(gate.name, gate.params)
            # Apply the gate: rho -> U * rho * U_dagger
            rho = U @ rho @ U.conj().T
            
            # If noise is present, apply it after each gate
            if noise_prob > 0:
                rho = self._apply_depolarizing_noise(rho, noise_prob)
        
        return rho

    def _get_gate_matrix(self, gate_name: str, params: List[float]) -> np.ndarray:
        """Gets the matrix representation of a gate."""
        if gate_name in GATE_MATRICES:
            return GATE_MATRICES[gate_name]
        elif gate_name == 'rx':
            return _rx_matrix(params[0])
        elif gate_name == 'ry':
            return _ry_matrix(params[0])
        else:
            raise ValueError(f"Gate '{gate_name}' is not supported by this basic simulator.")

    def _apply_depolarizing_noise(self, rho: np.ndarray, p: float) -> np.ndarray:
        """Applies the single-qubit depolarizing noise channel."""
        identity = np.identity(2)
        return (1 - p) * rho + p * identity / 2