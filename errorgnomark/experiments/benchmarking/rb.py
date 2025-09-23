# # File Path: errorgnomark/experiments/benchmarking/rb.py
# # RESTRUCTURED into Standard and Interleaved RB experiments.

# import numpy as np
# from typing import List, Dict, Tuple, Optional

# from errorgnomark.backends.base_backend import BaseBackend
# from errorgnomark.circuits.circuit import QuantumCircuit, Gate
# from errorgnomark.experiments.gate_sets import CliffordGateSet
# from errorgnomark.analysis.benchmarking.rb_analysis import fit_rb_data, plot_rb_single, plot_rb_comparison

# class _RBEngine:
#     """Internal engine to generate and run RB circuits."""
#     def __init__(
#         self,
#         qubits: List[int],
#         depths: List[int],
#         circuits_per_depth: int,
#         gate_set: CliffordGateSet,
#         interleaved_gate: Optional[Gate] = None
#     ):
#         self.qubits = qubits
#         self.depths = depths
#         self.circuits_per_depth = circuits_per_depth
#         self.gate_set = gate_set
#         self.interleaved_gate = interleaved_gate
#         self.num_qubits = len(qubits)

#     def _generate_single_circuit(self, depth: int) -> QuantumCircuit:
#         """Generates one RB circuit (standard or interleaved)."""
#         forward_gates, inverse_stack = [], []
        
#         # Get inverse of the interleaved gate if it exists.
#         # This assumes the inverse is known in the gate_set's internal map.
#         interleaved_gate_inv = None
#         if self.interleaved_gate:
#             inv_name = self.gate_set._inverse_map.get(self.interleaved_gate.name)
#             if not inv_name:
#                 raise ValueError(f"Inverse for gate '{self.interleaved_gate.name}' not found.")
#             interleaved_gate_inv = Gate(name=inv_name, qubits=self.interleaved_gate.qubits)

#         for _ in range(depth):
#             fwd_layer, inv_layer = self.gate_set.get_random_clifford_and_inverse(self.qubits)
#             forward_gates.extend(fwd_layer)
#             inverse_stack.append(inv_layer)
            
#             # If interleaved, add the target gate and its inverse to the stacks
#             if self.interleaved_gate and interleaved_gate_inv:
#                 forward_gates.append(self.interleaved_gate)
#                 inverse_stack.append([interleaved_gate_inv])

#         inverse_gates = [gate for layer in reversed(inverse_stack) for gate in layer]
#         return QuantumCircuit(qubits=self.qubits, gates=forward_gates + inverse_gates)

#     def run(self, backend: BaseBackend, shots: int, verbose: bool = False) -> Dict[int, List[float]]:
#         """Runs all circuits for all depths and returns survival probabilities."""
#         survivals: Dict[int, List[float]] = {depth: [] for depth in self.depths}
#         total_circs = len(self.depths) * self.circuits_per_depth
        
#         count = 0
#         for depth in self.depths:
#             for _ in range(self.circuits_per_depth):
#                 count += 1
#                 if verbose:
#                     print(f"Running circuit {count}/{total_circs} (Depth: {depth})...", end='\r')
                
#                 circuit = self._generate_single_circuit(depth)
#                 _, noisy_counts = backend.run(circuit, shots)
                
#                 total_shots = sum(noisy_counts.values())
#                 if total_shots == 0:
#                     prob = 0.0
#                 else:
#                     ground_state_str = '0' * self.num_qubits
#                     prob = noisy_counts.get(ground_state_str, 0) / total_shots
#                 survivals[depth].append(prob)
#         if verbose: print() # Newline after progress bar
#         return survivals

# # --- USER-FACING CLASS 1: Standard RB ---
# class StandardRBExperiment:
#     """Performs a standard RB experiment to find the Error Per Clifford (EPC)."""
#     def __init__(
#         self,
#         qubits: List[int],
#         depths: Optional[List[int]] = None,
#         circuits_per_depth: int = 30,
#     ):
#         self.qubits = qubits
#         self.num_qubits = len(qubits)
#         self.circuits_per_depth = circuits_per_depth
        
#         if depths is None:
#             self.depths = [1, 10, 20, 40, 60, 80] if self.num_qubits == 1 else [1, 5, 10, 15, 20, 25]
#         else:
#             self.depths = depths
        
#         # For standard RB, we just use the default CliffordGateSet
#         self.gate_set = CliffordGateSet()

#     def run_and_fit(self, backend: BaseBackend, shots: int = 4096, verbose: bool = False, plot: bool = False) -> Dict:
#         if verbose:
#             print(f"--- Running Standard {self.num_qubits}-Qubit RB ---")
        
#         engine = _RBEngine(self.qubits, self.depths, self.circuits_per_depth, self.gate_set)
#         survivals = engine.run(backend, shots, verbose)
        
#         if verbose: print("Fitting standard RB data...")
#         fit_results = fit_rb_data(survivals, self.num_qubits)
        
#         if verbose:
#             if fit_results['fit_successful']:
#                 print(f"Fit successful. EPC = {fit_results['epc']:.3e}")
#             else:
#                 print("Fit failed.")
        
#         if plot:
#             if verbose: print("Generating plot...")
#             plot_rb_single(fit_results, self.num_qubits)
            
#         return fit_results

# # --- USER-FACING CLASS 2: Interleaved RB ---
# class InterleavedRBExperiment:
#     """Performs an interleaved RB experiment to find the error of a specific target gate."""
#     def __init__(
#         self,
#         qubits: List[int],
#         target_gate_name: str,
#         depths: Optional[List[int]] = None,
#         circuits_per_depth: int = 50,
#     ):
#         self.qubits = qubits
#         self.num_qubits = len(qubits)
#         self.target_gate_name = target_gate_name
#         self.target_gate = Gate(name=target_gate_name, qubits=tuple(qubits))
#         self.circuits_per_depth = circuits_per_depth

#         if len(self.target_gate.qubits) != self.num_qubits:
#             raise ValueError(f"Target gate '{target_gate_name}' acts on {len(self.target_gate.qubits)} qubits, "
#                              f"but experiment is for {self.num_qubits} qubits.")

#         if depths is None:
#             self.depths = [1, 10, 20, 30, 40, 50] if self.num_qubits == 1 else [1, 4, 8, 12, 16, 20]
#         else:
#             self.depths = depths
            
#         # The gate set needs to know about the target gate for its inverse
#         self.gate_set = CliffordGateSet()

#     def run_and_fit(self, backend: BaseBackend, shots: int = 8096, verbose: bool = False, plot: bool = False) -> Dict:
#         if verbose:
#             print(f"\n--- Running Interleaved {self.num_qubits}-Qubit RB for gate '{self.target_gate_name}' ---")

#         # 1. Run Standard RB experiment
#         if verbose: print("[Step 1/2] Running Standard RB reference experiment...")
#         std_engine = _RBEngine(self.qubits, self.depths, self.circuits_per_depth, self.gate_set)
#         std_survivals = std_engine.run(backend, shots, verbose)
#         results_std = fit_rb_data(std_survivals, self.num_qubits)
#         if verbose and results_std['fit_successful']:
#             print(f"Standard EPC = {results_std['epc']:.3e}")

#         # 2. Run Interleaved RB experiment
#         if verbose: print(f"\n[Step 2/2] Running Interleaved RB experiment with '{self.target_gate_name}'...")
#         int_engine = _RBEngine(self.qubits, self.depths, self.circuits_per_depth, self.gate_set, self.target_gate)
#         int_survivals = int_engine.run(backend, shots, verbose)
#         results_int = fit_rb_data(int_survivals, self.num_qubits)
#         if verbose and results_int['fit_successful']:
#             print(f"Interleaved EPC = {results_int['epc']:.3e}")

#         # 3. Calculate target gate error
#         gate_error = -1.0
#         if results_std['fit_successful'] and results_int['fit_successful']:
#             d = 2**self.num_qubits
#             epc_std = results_std['epc']
#             epc_int = results_int['epc']
#             gate_error = (d - 1) * (epc_int - epc_std) / d
#             if verbose:
#                 print("\n--- Results ---")
#                 print(f"Error of gate '{self.target_gate_name}' (r_G) = {gate_error:.3e}")
#         elif verbose:
#             print("\nCould not calculate gate error because one or both fits failed.")

#         if plot:
#             if verbose: print("Generating comparison plot...")
#             # We need to pass the raw survival data to the plot function for std dev bars
#             results_std['raw_survivals'] = std_survivals
#             results_int['raw_survivals'] = int_survivals
#             plot_rb_comparison(results_std, results_int, self.num_qubits, self.target_gate_name)

#         return {
#             'gate_error': gate_error,
#             'standard_results': results_std,
#             'interleaved_results': results_int,
#         }



# File Path: errorgnomark/experiments/benchmarking/rb.py
# MODIFIED: Implemented flexible interleaved gates, robust inverse calculation,
# and set uniform Clifford sampling as the default behavior.

import numpy as np
from typing import List, Dict, Tuple, Optional, Union
import random
from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.circuits.circuit import QuantumCircuit, Gate
from errorgnomark.experiments.gate_sets import CliffordGateSet
from errorgnomark.analysis.benchmarking.rb_analysis import fit_rb_data, plot_rb_single, plot_rb_comparison

class _RBEngine:
    """Internal engine to generate and run RB circuits."""
    def __init__(
        self,
        qubits: List[int],
        depths: List[int],
        circuits_per_depth: int,
        gate_set: Optional[CliffordGateSet] = None,
        interleaved_gates: Optional[Union[Gate, List[Gate]]] = None
    ):
        self.qubits = qubits
        self.depths = depths
        self.circuits_per_depth = circuits_per_depth
        self.num_qubits = len(qubits)

        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        # [[[ MODIFICATION 1: SET UNIFORM SAMPLING AS DEFAULT ]]]
        # If no gate set is provided, create one that uses uniform sampling from C24.
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        if gate_set is None:
            self.gate_set = CliffordGateSet(generation_method='uniform_from_c24_decompositions')
        else:
            self.gate_set = gate_set

        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        # [[[ MODIFICATION 2: FLEXIBLE INTERLEAVED GATES (SINGLE OR LIST) ]]]
        # Normalize the interleaved_gates parameter to always be a list.
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        if interleaved_gates is None:
            self.interleaved_gates: List[Gate] = []
        elif isinstance(interleaved_gates, Gate):
            self.interleaved_gates = [interleaved_gates]
        else:
            self.interleaved_gates = interleaved_gates

    def _generate_single_circuit(self, depth: int, seed: Optional[int] = None) -> QuantumCircuit:
        """
        Generates one RB circuit (standard or interleaved) for a given depth.
        
        Args:
            depth (int): The number of Clifford elements in the circuit.
            seed (Optional[int]): A seed for the random number generator to ensure reproducibility.
        
        Returns:
            QuantumCircuit: The generated RB circuit.
        """
        rng = random.Random(seed)
        forward_gates, inverse_stack = [], []
        
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        # [[[ MODIFICATION 3: ROBUST INVERSE CALCULATION ]]]
        # Calculate the inverse of the entire interleaved sequence using gate.inverse().
        # The inverse of (G_n * ... * G_1) is (G_1_inv * ... * G_n_inv).
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        interleaved_gates_inv: List[Gate] = []
        if self.interleaved_gates:
            interleaved_gates_inv = [g.inverse() for g in reversed(self.interleaved_gates)]

        for i in range(depth):
            # Use a unique seed for each layer to ensure randomness between layers
            layer_seed = rng.randint(0, 2**32 - 1)
            fwd_layer, inv_layer = self.gate_set.get_random_clifford_and_inverse(self.qubits, seed=layer_seed)
            
            forward_gates.extend(fwd_layer)
            inverse_stack.append(inv_layer)
            
            # If interleaved, add the target gate sequence and its inverse to the stacks
            if self.interleaved_gates:
                forward_gates.extend(self.interleaved_gates)
                inverse_stack.append(interleaved_gates_inv)

        # Build the final recovery Clifford from the inverse stack
        inverse_gates = [gate for layer in reversed(inverse_stack) for gate in layer]
        
        # Create the full circuit
        circuit = QuantumCircuit(qubits=self.qubits, gates=forward_gates + inverse_gates)
        circuit.measure_all()
        return circuit

    def run(self, backend: BaseBackend, shots: int, verbose: bool = False) -> Dict[int, List[float]]:
        """Runs all circuits for all depths and returns survival probabilities."""
        survivals: Dict[int, List[float]] = {depth: [] for depth in self.depths}
        total_circs = len(self.depths) * self.circuits_per_depth
        
        count = 0
        for depth in self.depths:
            for _ in range(self.circuits_per_depth):
                count += 1
                if verbose:
                    print(f"Running circuit {count}/{total_circs} (Depth: {depth})...", end='\r')
                
                circuit = self._generate_single_circuit(depth)
                _, noisy_counts = backend.run(circuit, shots)
                
                total_shots = sum(noisy_counts.values())
                if total_shots == 0:
                    prob = 0.0
                else:
                    ground_state_str = '0' * self.num_qubits
                    prob = noisy_counts.get(ground_state_str, 0) / total_shots
                survivals[depth].append(prob)
        if verbose: print() # Newline after progress bar
        return survivals

# --- USER-FACING CLASS 1: Standard RB ---
class StandardRBExperiment:
    """Performs a standard RB experiment to find the Error Per Clifford (EPC)."""
    def __init__(
        self,
        qubits: List[int],
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = 30,
    ):
        self.qubits = qubits
        self.num_qubits = len(qubits)
        self.circuits_per_depth = circuits_per_depth
        
        if depths is None:
            self.depths = [1, 10, 20, 40, 60, 80] if self.num_qubits == 1 else [1, 5, 10, 15, 20, 25]
        else:
            self.depths = depths
        
        # For standard RB, we just use the default CliffordGateSet
        self.gate_set = CliffordGateSet()

    def run_and_fit(self, backend: BaseBackend, shots: int = 4096, verbose: bool = False, plot: bool = False) -> Dict:
        if verbose:
            print(f"--- Running Standard {self.num_qubits}-Qubit RB ---")
        
        engine = _RBEngine(self.qubits, self.depths, self.circuits_per_depth, self.gate_set)
        survivals = engine.run(backend, shots, verbose)
        
        if verbose: print("Fitting standard RB data...")
        fit_results = fit_rb_data(survivals, self.num_qubits)
        
        if verbose:
            if fit_results['fit_successful']:
                print(f"Fit successful. EPC = {fit_results['epc']:.3e}")
            else:
                print("Fit failed.")
        
        if plot:
            if verbose: print("Generating plot...")
            plot_rb_single(fit_results, self.num_qubits)
            
        return fit_results

# --- USER-FACING CLASS 2: Interleaved RB ---
class InterleavedRBExperiment:
    """Performs an interleaved RB experiment to find the error of a specific target gate."""
    def __init__(
        self,
        qubits: List[int],
        target_gate_name: str,
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = 50,
    ):
        self.qubits = qubits
        self.num_qubits = len(qubits)
        self.target_gate_name = target_gate_name
        self.target_gate = Gate(name=target_gate_name, qubits=tuple(qubits))
        self.circuits_per_depth = circuits_per_depth

        if len(self.target_gate.qubits) != self.num_qubits:
            raise ValueError(f"Target gate '{target_gate_name}' acts on {len(self.target_gate.qubits)} qubits, "
                             f"but experiment is for {self.num_qubits} qubits.")

        if depths is None:
            self.depths = [1, 10, 20, 30, 40, 50] if self.num_qubits == 1 else [1, 4, 8, 12, 16, 20]
        else:
            self.depths = depths
            
        # The gate set needs to know about the target gate for its inverse
        self.gate_set = CliffordGateSet()

    def run_and_fit(self, backend: BaseBackend, shots: int = 8096, verbose: bool = False, plot: bool = False) -> Dict:
        if verbose:
            print(f"\n--- Running Interleaved {self.num_qubits}-Qubit RB for gate '{self.target_gate_name}' ---")

        # 1. Run Standard RB experiment
        if verbose: print("[Step 1/2] Running Standard RB reference experiment...")
        std_engine = _RBEngine(self.qubits, self.depths, self.circuits_per_depth, self.gate_set)
        std_survivals = std_engine.run(backend, shots, verbose)
        results_std = fit_rb_data(std_survivals, self.num_qubits)
        if verbose and results_std['fit_successful']:
            print(f"Standard EPC = {results_std['epc']:.3e}")

        # 2. Run Interleaved RB experiment
        if verbose: print(f"\n[Step 2/2] Running Interleaved RB experiment with '{self.target_gate_name}'...")
        int_engine = _RBEngine(self.qubits, self.depths, self.circuits_per_depth, self.gate_set, self.target_gate)
        int_survivals = int_engine.run(backend, shots, verbose)
        results_int = fit_rb_data(int_survivals, self.num_qubits)
        if verbose and results_int['fit_successful']:
            print(f"Interleaved EPC = {results_int['epc']:.3e}")

        # 3. Calculate target gate error
        gate_error = -1.0
        if results_std['fit_successful'] and results_int['fit_successful']:
            d = 2**self.num_qubits
            epc_std = results_std['epc']
            epc_int = results_int['epc']
            gate_error = (d - 1) * (epc_int - epc_std) / d
            if verbose:
                print("\n--- Results ---")
                print(f"Error of gate '{self.target_gate_name}' (r_G) = {gate_error:.3e}")
        elif verbose:
            print("\nCould not calculate gate error because one or both fits failed.")

        if plot:
            if verbose: print("Generating comparison plot...")
            # We need to pass the raw survival data to the plot function for std dev bars
            results_std['raw_survivals'] = std_survivals
            results_int['raw_survivals'] = int_survivals
            plot_rb_comparison(results_std, results_int, self.num_qubits, self.target_gate_name)

        return {
            'gate_error': gate_error,
            'standard_results': results_std,
            'interleaved_results': results_int,
        }

