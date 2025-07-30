# errorgnomark/backends/dummy_backend.py
from typing import Dict, Any, List
import numpy as np

# We assume the QuantumCircuit definition is in this path.
from ..circuits.circuit import QuantumCircuit

class DummyBackend:
    """
    A dummy backend for testing and demonstration purposes.
    
    It uses an internal density matrix simulator and can apply
    configurable depolarizing noise.
    """
    def __init__(self, depolarizing_error: float = 0.0, seed: int = None):
        """
        Initializes the dummy backend.

        Args:
            depolarizing_error (float): The single-qubit depolarizing error rate 
                                        applied after each gate.
            seed (int, optional): Seed for the simulation's randomness. Defaults to None.
        """
        if not (0 <= depolarizing_error <= 1):
            raise ValueError("Depolarizing error must be between 0 and 1.")
        
        self.noise_level = depolarizing_error
        # The backend holds an instance of the internal simulator logic.
        self._simulator = _BasicSimulatorLogic() 
        print(f"DummyBackend initialized with depolarizing error = {self.noise_level:.3f}")

    def run(self, circuit: QuantumCircuit) -> Dict[str, Any]:
        """
        Executes a single quantum circuit.

        This method performs both ideal and noisy simulations to facilitate 
        benchmarks like XEB.

        Args:
            circuit: The QuantumCircuit object to execute.

        Returns:
            A dictionary containing the raw results, with the format:
            {
                'ideal_probs': np.ndarray,
                'noisy_probs': np.ndarray
            }
        """
        # Ideal simulation
        ideal_probs = self._simulator.simulate(circuit)
        
        # Noisy simulation
        noisy_probs = self._simulator.simulate_noisy(circuit, self.noise_level)

        return {
            'ideal_probs': ideal_probs,
            'noisy_probs': noisy_probs
        }

# To keep the backend file clean, the simulator logic is encapsulated in a 
# "private" class. This aligns with the principle of hiding implementation details.

class _BasicSimulatorLogic:
    """Internal simulator logic, using density matrices."""
    def __init__(self):
        self._gate_matrices = {
            'h': 1/np.sqrt(2) * np.array([[1, 1], [1, -1]]),
            's': np.array([[1, 0], [0, 1j]]),
            'x': np.array([[0, 1], [1, 0]]),
            'y': np.array([[0, -1j], [1j, 0]]),
            'z': np.array([[1, 0], [0, -1]]),
            'i': np.identity(2)
        }

    def _get_gate_matrix(self, gate_name: str, params: List[float]) -> np.ndarray:
        # This can be extended for parameterized gates like rx, ry
        return self._gate_matrices[gate_name]

    def _apply_depolarizing_noise(self, rho: np.ndarray, p: float) -> np.ndarray:
        return (1 - p) * rho + p * np.identity(2) / 2

    def _run(self, circuit: QuantumCircuit, noise_prob: float = 0.0) -> np.ndarray:
        rho = np.zeros((2, 2), dtype=np.complex128)
        rho[0, 0] = 1
        for gate in circuit.gates:
            U = self._get_gate_matrix(gate.name, gate.params)
            rho = U @ rho @ U.conj().T
            if noise_prob > 0:
                rho = self._apply_depolarizing_noise(rho, noise_prob)
        return rho

    def simulate(self, circuit: QuantumCircuit) -> np.ndarray:
        final_rho = self._run(circuit, 0.0)
        return np.real(final_rho.diagonal())

    def simulate_noisy(self, circuit: QuantumCircuit, depolarizing_prob: float) -> np.ndarray:
        final_rho = self._run(circuit, depolarizing_prob)
        return np.real(final_rho.diagonal())