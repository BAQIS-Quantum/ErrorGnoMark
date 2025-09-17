# errorgnomark/experiments/benchmarking/_base_benchmarking.py

from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any, Optional, Tuple, Callable

from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.circuits.circuit import QuantumCircuit
from errorgnomark.experiments.base_experiment import BaseExperiment


class _BaseBenchmarkingExperiment(BaseExperiment, ABC):
    """
    An abstract base class for benchmarking experiments like RB and MRB.

    This class provides a standardized `run_and_fit` workflow that handles
    running circuits for specified qubit groups, analyzing the results using
    experiment-specific functions, and optionally plotting the results.

    It inherits from the top-level `BaseExperiment`.
    """
    def __init__(self,
                 qubits: Union[List[int], List[Tuple[int, ...]]],
                 depths: List[int],
                 circuits_per_depth: int):
        
        if not isinstance(qubits, list) or not qubits:
            raise TypeError("`qubits` must be a non-empty list of integers or tuples.")
        self.qubits = qubits
        self.depths = depths
        self.circuits_per_depth = circuits_per_depth

    @abstractmethod
    def _generate_single_circuit(self, group: Union[int, Tuple[int, ...]], depth: int) -> QuantumCircuit:
        """Generates a single random circuit for a given group and depth."""
        pass

    @abstractmethod
    def _calculate_survival_probability(self, counts: Dict[str, int], group: Union[int, Tuple[int, ...]]) -> float:
        """Calculates the survival probability from the measurement counts."""
        pass

    @abstractmethod
    def _get_analysis_functions(self) -> Tuple[Callable, Callable]:
        """Returns the specific (fit_func, plot_func) for the experiment."""
        pass

    def run_single_group(self, 
                         group: Union[int, Tuple[int, ...]], 
                         backend: BaseBackend, 
                         shots: int, 
                         verbose: bool) -> Dict[int, List[float]]:
        """
        Runs the experiment for a single qubit group and returns survival data.
        """
        survival_data: Dict[int, List[float]] = {d: [] for d in self.depths}
        for depth in self.depths:
            if verbose:
                print(f"  Depth {depth} ({self.circuits_per_depth} circuits): ", end='', flush=True)
            
            for _ in range(self.circuits_per_depth):
                circuit = self._generate_single_circuit(group, depth)
                _, noisy_counts = backend.run(circuit, shots=shots)
                survival_prob = self._calculate_survival_probability(noisy_counts, group)
                survival_data[depth].append(survival_prob)
                if verbose:
                    print(".", end='', flush=True)
            if verbose:
                print(" Done.")
        return survival_data

    def run_and_fit(self,
                    backend: BaseBackend,
                    shots: int = 1024,
                    plot_decay: bool = False,
                    verbose: bool = False) -> Dict[Union[int, Tuple], Dict]:
        """
        Executes the full benchmark: runs circuits, fits the decay, and optionally plots.
        """
        all_results = {}
        fit_func, plot_func = self._get_analysis_functions()
        
        for group in self.qubits:
            group_key = group if isinstance(group, tuple) else (group,)
            num_qubits = len(group_key) if isinstance(group_key, tuple) else 1
            
            if verbose:
                print(f"\n--- Running experiment for qubit group: {group} ---")

            # Step 1: Data Collection
            survival_data = self.run_single_group(group, backend, shots, verbose)

            # Step 2: Data Analysis
            if verbose:
                print(f"  Analyzing data for group {group}...")
            fit_results = fit_func(survival_data, num_qubits)
            all_results[group] = fit_results

            # Step 3: Plotting
            if plot_decay and fit_results['fit_successful']:
                if verbose:
                    print(f"  Plotting decay curve for group {group}...")
                plot_func(survival_data, fit_results, num_qubits)
            elif plot_decay:
                 print(f"  Skipping plot for group {group} because curve fitting failed.")

        return all_results