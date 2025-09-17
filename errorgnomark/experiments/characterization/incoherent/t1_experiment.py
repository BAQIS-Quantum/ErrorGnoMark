# File Path: errorgnomark/experiments/characterization/incoherent/t1_experiment.py
# MODIFIED to be compatible with the immutable "golden" runner.py

from typing import List, Dict, Any, Tuple

import numpy as np

from errorgnomark.analysis.results import CoherenceAnalysisResult
from errorgnomark.circuits.circuit_operations import t1_circuit
from errorgnomark.experiments.base_experiment import BaseExperiment
from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.analysis.characterization.incoherent_analysis import analyze_t1
# We need to import QuantumCircuit for the type hint
from errorgnomark.circuits.circuit import QuantumCircuit

class T1Experiment(BaseExperiment):
    """
    An experiment to measure the T1 relaxation time of a qubit.
    """
    def __init__(self, qubits: List[int], delays: np.ndarray, backend: BaseBackend):
        """
        Initializes the T1 experiment.

        Args:
            qubits: A list containing the single qubit to be measured.
            delays: A numpy array of delay times (in seconds) to be tested.
            backend: The quantum backend to run the circuits on.
        """
        if len(qubits) != 1:
            raise ValueError("T1 experiment is a single-qubit experiment.")
        
        super().__init__() 
        self.qubits = qubits
        self.backend = backend
        self.delays = delays
        self.name = "T1 Experiment"

    # <<< 主要修改点：此方法现在返回 List[QuantumCircuit] 以满足 Runner 的要求
    def generate_circuits(self) -> List[QuantumCircuit]:
        """
        Generates the circuits for the T1 experiment. This method now returns a
        list of QuantumCircuit objects, as required by the golden runner.
        """
        circuit_list: List[QuantumCircuit] = []
        qubit = self.qubits[0]
        for delay in self.delays:
            # Create the circuit for the current delay
            circuit = t1_circuit(qubit, delay)
            # Append the circuit object directly to the list
            circuit_list.append(circuit)
        return circuit_list

    def analyze(self, results: List[Tuple[Dict[str, Any], np.ndarray]]) -> CoherenceAnalysisResult:
        """
        Analyzes the results of the T1 experiment to find the T1 time.
        """
        # This method is kept for API consistency, but the demo script
        # calls the standalone analyze_t1 function.
        return analyze_t1(results, self.qubits)