# errorgnomark/experiments/benchmarking/xeb.py
from typing import List

from ..base_experiment import BaseExperiment
from ...circuits.circuit import QuantumCircuit, Gate
# [MODIFICATION 1]: Import the new gate set classes from the correct location.
from ..gate_sets import CliffordGateSet, XYGateSet

class XEBExperiment(BaseExperiment):
    """
    Defines the circuits required to run a Cross-Entropy Benchmarking (XEB) experiment.
    """
    def __init__(self, qubits: List[int], depths: List[int], num_circuits: int, gate_set: str = "clifford"):
        super().__init__()
        if len(qubits) != 1:
            raise NotImplementedError("This XEB experiment currently only supports a single qubit.")
        self.qubits = qubits
        self.depths = depths
        self.num_circuits = num_circuits
        
        # [MODIFICATION 2]: Instantiate the correct gate set object based on the string name.
        if gate_set == "clifford":
            self.gate_set = CliffordGateSet()
        elif gate_set == "xy":
            self.gate_set = XYGateSet()
        else:
            raise ValueError(f"Unsupported gate set: {gate_set}")
        
        print(f"--- Generating circuits for {len(qubits)}Q-XEB (Qubit: {qubits}, GateSet: {type(self.gate_set).__name__}) ---")

    def generate_circuits(self) -> List[QuantumCircuit]:
        """
        Generates random circuits using the selected gate set.
        """
        circuits = []
        target_qubit = self.qubits[0] # We operate on the single qubit

        for depth in self.depths:
            print(f"  Generating {self.num_circuits} circuits of depth {depth}...")
            for _ in range(self.num_circuits):
                gates: List[Gate] = []
                # [MODIFICATION 3]: The circuit generation loop is now much cleaner.
                for _ in range(depth):
                    # Get a random Gate object from our gate set
                    random_gate = self.gate_set.get_random_gate(qubit=target_qubit)
                    gates.append(random_gate)
                
                circuit = QuantumCircuit(qubits=self.qubits, gates=gates)
                circuits.append(circuit)
        
        print(f"Total circuits generated: {len(circuits)}")
        return circuits