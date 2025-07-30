# errorgnomark/experiments/benchmarking/xeb.py

from typing import List, Union, Dict, Type

from errorgnomark.circuits.circuit import QuantumCircuit
from errorgnomark.experiments.benchmarking.gate_sets import (
    SingleQubitGateSet, 
    CliffordGateSet, 
    XYGateSet
)

# A registry mapping string names to pre-defined gate set classes
_PREDEFINED_GATE_SETS: Dict[str, Type[SingleQubitGateSet]] = {
    "clifford": CliffordGateSet,
    "xy": XYGateSet,
}


class XEBExperiment:
    """
    Generates circuit lists for a Cross-Entropy Benchmarking (XEB) experiment.

    This class is parameterized by a gate set, allowing for flexible generation
    of random circuits for benchmarking fidelity.
    """
    def __init__(
        self,
        qubits: List[int],
        depths: List[int],
        num_circuits: int,
        gate_set: Union[str, SingleQubitGateSet]
    ):
        """
        Initializes the XEB experiment.

        Args:
            qubits (List[int]): A list of qubits to test. For single-qubit XEB,
                                this should be a list with one element, e.g., [0].
            depths (List[int]): A list of circuit depths to generate.
            num_circuits (int): The number of random circuits to generate per depth.
            gate_set (Union[str, SingleQubitGateSet]): The gate set to use.
                - Can be a string name of a pre-defined set (e.g., "clifford", "xy").
                - Can be an instance of a user-defined class that inherits from
                  `SingleQubitGateSet`.
        """
        if len(qubits) != 1:
            # This implementation is focused on single-qubit XEB as requested
            raise ValueError("This XEBExperiment currently supports single-qubit only.")
        
        self.qubit = qubits[0]
        self.depths = depths
        self.num_circuits = num_circuits
        
        # --- Gate Set Initialization Logic ---
        if isinstance(gate_set, str):
            gate_set_name = gate_set.lower()
            if gate_set_name not in _PREDEFINED_GATE_SETS:
                raise ValueError(
                    f"Unknown pre-defined gate set '{gate_set}'. "
                    f"Available options are: {list(_PREDEFINED_GATE_SETS.keys())}"
                )
            self.gate_set: SingleQubitGateSet = _PREDEFINED_GATE_SETS[gate_set_name]()
        elif isinstance(gate_set, SingleQubitGateSet):
            self.gate_set = gate_set
        else:
            raise TypeError(
                "gate_set must be a string or an instance of SingleQubitGateSet."
            )
            
        self.experiment_type = f"1Q-XEB (Qubit: {self.qubit}, GateSet: {self.gate_set.__class__.__name__})"

    def generate_circuits(self) -> List[QuantumCircuit]:
        """
        Generates the list of random quantum circuits for the experiment.

        Returns:
            List[QuantumCircuit]: A list of generated circuits.
        """
        print(f"--- Generating circuits for {self.experiment_type} ---")
        all_circuits = []
        for depth in self.depths:
            print(f"  Generating {self.num_circuits} circuits of depth {depth}...")
            for _ in range(self.num_circuits):
                circuit = QuantumCircuit(num_qubits=1)
                for _ in range(depth):
                    random_gate = self.gate_set.get_random_gate(self.qubit)
                    circuit.add_gate(random_gate)
                all_circuits.append(circuit)
        
        print(f"Total circuits generated: {len(all_circuits)}")
        return all_circuits