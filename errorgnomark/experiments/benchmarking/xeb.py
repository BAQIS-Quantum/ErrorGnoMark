# File Path: errorgnomark/experiments/benchmarking/xeb.py (Corrected Version)

import abc
import itertools
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

# --- Core Dependencies ---
from errorgnomark.experiments.base_experiment import BaseExperiment
from errorgnomark.analysis.benchmarking.xeb_analysis import (analyze_xeb_fidelity,
                                                             fit_xeb_fidelity_decay)
from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.circuits.circuit import Gate, QuantumCircuit
from errorgnomark.circuits.visualization import format_circuit_as_string
# MODIFIED: We now import the factory function directly
from errorgnomark.experiments.gate_sets import BaseGateSet, TwoQubitGateSet, get_gate_set


# --- Helper Validation Functions (Unchanged) ---
def _validate_list_of_integers(qubits: Any, var_name: str):
    if not isinstance(qubits, list) or not all(isinstance(q, int) for q in qubits):
        raise TypeError(f"`{var_name}` must be a list of integers.")

def _validate_list_of_qubit_pairs(pairs: Any, var_name: str):
    if not isinstance(pairs, list) or not all(
            isinstance(p, tuple) and len(p) == 2 and all(isinstance(q, int) for q in p)
            for p in pairs
    ):
        raise TypeError(f"`{var_name}` must be a list of 2-element integer tuples.")


# --- Atomic Task (MODIFIED TO FIX BUG) ---
class StandardXEBInstance(BaseExperiment):
    def __init__(self,
                 qubits: Union[int, List[int]],
                 depth: int = 40,
                 gate_set: Union[str, Dict, BaseGateSet] = "clifford",
                 topology: Optional[List[Tuple[int, int]]] = None,
                 backend: Optional[BaseBackend] = None,
                 shots: int = 8096):
        super().__init__()
        if isinstance(qubits, int):
            self.qubits = list(range(qubits))
        else:
            self.qubits = qubits
        _validate_list_of_integers(self.qubits, "qubits")
        if topology: _validate_list_of_qubit_pairs(topology, "topology")
        self.depth = depth

        ### [BUG FIX EXPLANATION] ###
        # The original code likely just assigned `self.gate_set = gate_set`.
        # When a string like "clifford" was passed, `self.gate_set` became a string.
        # This caused `isinstance(self.gate_set, TwoQubitGateSet)` in the
        # `_generate_circuit` method to always fail, preventing any 2Q gates
        # from being added to the circuit.
        #
        # The corrected code below uses the `get_gate_set` factory function.
        # This ensures that `self.gate_set` is ALWAYS a proper GateSet object,
        # never just a string. This is the critical fix.
        self.gate_set = get_gate_set(gate_set)
        
        self.topology = topology if topology is not None else self._get_default_topology()
        self.backend = backend
        self.shots = shots
        self.last_circuit: Optional[QuantumCircuit] = None

    def _get_default_topology(self) -> List[Tuple[int, int]]:
        if len(self.qubits) < 2: return []
        return list(itertools.combinations(self.qubits, 2))

    ### [CIRCUIT STRUCTURE ANALYSIS] ###
    # This method implements the core XEB circuit generation logic.
    # Your understanding is correct: it alternates between 1Q and 2Q gate layers.
    def _generate_circuit(self) -> QuantumCircuit:
        gates: List[Gate] = []
        # The loop runs `depth` times. Each iteration adds one "cycle" or "layer".
        for _ in range(self.depth):
            # 1. Add a layer of random single-qubit gates on all specified qubits.
            gates.extend(self.gate_set.get_random_1q_layer(qubits=self.qubits))
            
            # 2. If a topology is provided AND the gate set is capable of 2Q gates...
            if self.topology and isinstance(self.gate_set, TwoQubitGateSet):
                # ...then add a layer of two-qubit gates.
                # This is the part that was failing due to the bug.
                gates.extend(self.gate_set.get_random_2q_layer(topology=self.topology))
                
        return QuantumCircuit(qubits=self.qubits, gates=gates)

    def run(self, backend: Optional[BaseBackend] = None, shots: Optional[int] = None) -> float:
        effective_backend = backend if backend is not None else self.backend
        if effective_backend is None: raise ValueError("A backend must be provided.")
        effective_shots = shots if shots is not None else self.shots
        circuit = self._generate_circuit()
        self.last_circuit = circuit
        ideal_counts, noisy_counts = effective_backend.run(circuit, shots=effective_shots)
        return analyze_xeb_fidelity(ideal_counts, noisy_counts)

    def print_last_circuit(self):
        print(f"\n--- Circuit Diagram (Qubits: {self.qubits}, Depth: {self.depth}) ---")
        if self.last_circuit is None:
            print("No circuit has been run yet. Call the `run()` method first.")
            return
        circuit_diagram = format_circuit_as_string(self.last_circuit)
        print(circuit_diagram)
        print("--- End of Diagram ---")


# --- Scheduler Base Class (Unchanged) ---
class BaseGateErrorEstimation(BaseExperiment, abc.ABC):
    def __init__(self,
                 depths: List[int],
                 num_circuits: int,
                 gate_set_spec: Union[str, Dict, BaseGateSet],
                 verbose: bool = False,
                 backend: Optional[BaseBackend] = None):
        super().__init__()
        self.depths = depths
        self.num_circuits = num_circuits
        self.gate_set_spec = gate_set_spec
        self.verbose = verbose
        self.backend = backend

    def _resolve_gate_set_instance(self) -> BaseGateSet:
        return get_gate_set(self.gate_set_spec)

    @abc.abstractmethod
    def run_and_fit(self, backend: Optional[BaseBackend] = None, shots: Optional[int] = None,
                    verbose: Optional[bool] = None, return_detailed: bool = False) -> Union[float, Dict]:
        pass


# --- SingleQubitGateError (Unchanged) ---
class SingleQubitGateError(BaseGateErrorEstimation):
    def __init__(self, qubits_to_test: List[int], depths: List[int] = [  1,  10,  19,  28,  37,  46,  55,  64,  73,  82,  91, 100], num_circuits: int = 50, gate_set: Union[str, Dict, BaseGateSet] = "clifford", verbose: bool = False, backend: Optional[BaseBackend] = None):
        super().__init__(depths, num_circuits, gate_set, verbose, backend)
        _validate_list_of_integers(qubits_to_test, "qubits_to_test")
        self.qubits_to_test = qubits_to_test
    def run_and_fit(self, backend: Optional[BaseBackend] = None, shots: int = 1024, verbose: Optional[bool] = None, return_detailed: bool = False) -> Union[float, Dict[int, Dict]]:
        effective_backend = backend if backend is not None else self.backend
        if effective_backend is None: raise ValueError("A backend must be provided.")
        is_verbose = self.verbose if verbose is None else verbose
        if is_verbose: print(f"--- Starting Single-Qubit Gate Error Estimation for qubits {self.qubits_to_test} ---")
        gate_set_instance = self._resolve_gate_set_instance()
        results_by_qubit = {}
        for qubit in self.qubits_to_test:
            if is_verbose: print(f"\nEstimating error for qubit {qubit}...")
            fidelities_for_fit = defaultdict(list)
            for depth in self.depths:
                if is_verbose: print(f"  Running depth {depth} ({self.num_circuits} circuits)...")
                for _ in range(self.num_circuits):
                    task = StandardXEBInstance(qubits=[qubit], depth=depth, gate_set=gate_set_instance)
                    fidelities_for_fit[depth].append(task.run(effective_backend, shots))
            if is_verbose: print(f"Fitting decay curve for qubit {qubit}...")
            fit_results = fit_xeb_fidelity_decay(fidelities_for_fit)
            if return_detailed: results_by_qubit[qubit] = {'fit_results': fit_results, 'raw_fidelities': dict(fidelities_for_fit)}
            else: results_by_qubit[qubit] = fit_results
        if return_detailed: return results_by_qubit
        total_error = sum(data.get('error_per_gate', 0) for data in results_by_qubit.values())
        count = len(results_by_qubit)
        return total_error / count if count > 0 else 0.0


# --- TwoQubitGateError (Unchanged) ---
class TwoQubitGateError(BaseGateErrorEstimation):
    def __init__(self,
                 pairs_to_test: List[Tuple[int, int]],
                 depths: List[int] = [  1,  10,  19,  28,  37,  46,  55,  64,  73,  82,  91, 100],
                 num_circuits: int = 50,
                 gate_set: Union[str, Dict, BaseGateSet] = "clifford",
                 target_gate: Optional[str] = 'cz',
                 verbose: bool = False,
                 backend: Optional[BaseBackend] = None):
        super().__init__(depths, num_circuits, gate_set, verbose, backend)
        _validate_list_of_qubit_pairs(pairs_to_test, "pairs_to_test")
        self.pairs_to_test = pairs_to_test
        self.target_gate = target_gate.lower() if target_gate else None

    def run_and_fit(self, backend: Optional[BaseBackend] = None, shots: int = 1024, verbose: Optional[bool] = None,
                    return_detailed: bool = False) -> Union[float, Dict[Tuple[int, int], Dict]]:
        effective_backend = backend if backend is not None else self.backend
        if effective_backend is None: raise ValueError("A backend must be provided.")
        is_verbose = self.verbose if verbose is None else verbose

        if is_verbose:
            print(f"--- Starting Two-Qubit Gate Error Estimation for pairs {self.pairs_to_test} ---")
            if self.target_gate:
                print(f"--- Target 2Q Gate: '{self.target_gate.upper()}' ---")

        gate_set_instance = self._resolve_gate_set_instance()

        if self.target_gate and isinstance(gate_set_instance, TwoQubitGateSet):
            if is_verbose:
                original_gate = getattr(gate_set_instance, 'two_qubit_gate_name', 'N/A')
                print(f"  > Overriding gate set's default 2Q gate ('{original_gate}') with '{self.target_gate.upper()}'.")
            gate_set_instance.two_qubit_gate_name = self.target_gate
        
        results_by_pair = {}
        for pair in self.pairs_to_test:
            if is_verbose: print(f"\nEstimating error for pair {pair}...")
            fidelities_for_fit = defaultdict(list)
            for depth in self.depths:
                if is_verbose: print(f"  Running depth {depth} ({self.num_circuits} circuits)...")
                for _ in range(self.num_circuits):
                    # When creating the task, we correctly pass the gate_set_instance object
                    task = StandardXEBInstance(qubits=list(pair), depth=depth, gate_set=gate_set_instance,
                                               topology=[pair])
                    fidelities_for_fit[depth].append(task.run(effective_backend, shots))
            if is_verbose: print(f"Fitting decay curve for pair {pair}...")
            fit_results = fit_xeb_fidelity_decay(fidelities_for_fit)
            
            if return_detailed:
                results_by_pair[pair] = {
                    'fit_results': fit_results,
                    'raw_fidelities': dict(fidelities_for_fit)
                }
            else:
                results_by_pair[pair] = fit_results

        if return_detailed:
            return results_by_pair

        total_error = sum(data.get('error_per_gate', 0) for data in results_by_pair.values())
        count = len(results_by_pair)
        return total_error / count if count > 0 else 0.0