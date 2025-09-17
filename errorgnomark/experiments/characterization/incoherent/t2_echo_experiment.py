# File Path: errorgnomark/experiments/characterization/incoherent/t2_echo_experiment.py
# MODIFIED to create DELAY gates with a consistent parameter structure.

from typing import List
import numpy as np

from errorgnomark.experiments.base_experiment import BaseExperiment
from errorgnomark.circuits.circuit import QuantumCircuit, Gate

class T2EchoExperiment(BaseExperiment):
    """
    An experiment to measure the T2 (spin-spin relaxation) time using a spin echo sequence.
    The sequence is: H - Delay/2 - X - Delay/2 - H
    """
    def __init__(self, qubits: List[int], delays: np.ndarray, backend: 'BaseBackend'):
        if len(qubits) != 1:
            raise ValueError("T2 Echo experiment currently supports only a single qubit.")
        self.qubits = qubits
        self.delays = delays
        self.backend = backend
        self._name = "T2EchoExperiment"

    def generate_circuits(self) -> List[QuantumCircuit]:
        """
        Generates the list of quantum circuits for the T2 Echo experiment.
        """
        circuits = []
        target_qubit = self.qubits[0]

        for delay_us in self.delays:
            # Convert delay from microseconds (as in demo script) to seconds for the backend
            delay_s = delay_us * 1e-6
            half_delay_s = delay_s / 2.0
            
            # --- THIS IS THE FIX ---
            # The 'params' list should contain the float value directly, not a dictionary.
            gates = [
                Gate(name='H', qubits=(target_qubit,)),
                Gate(name='DELAY', qubits=(target_qubit,), params=[half_delay_s]),
                Gate(name='X', qubits=(target_qubit,)),
                Gate(name='DELAY', qubits=(target_qubit,), params=[half_delay_s]),
                Gate(name='H', qubits=(target_qubit,)),
                Gate(name='MEASURE', qubits=(target_qubit,)), # Add measure for consistency
            ]
            
            qc = QuantumCircuit(qubits=[target_qubit], gates=gates)
            qc.metadata = {'experiment': 'T2 Echo', 'delay': delay_us}
            circuits.append(qc)
            
        return circuits

    def analyze(self, results, **kwargs):
        raise NotImplementedError("Analysis for T2EchoExperiment is handled by a separate 'analyze_t2_echo' function.")