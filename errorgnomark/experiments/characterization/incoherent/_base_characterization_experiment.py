# errorgnomark/experiments/characterization/incoherent/_base_characterization_experiment.py

from abc import abstractmethod
from typing import List, Dict, Any, Tuple, Callable, Union
from dataclasses import dataclass
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.circuits.circuit import QuantumCircuit
from errorgnomark.experiments.base_experiment import BaseExperiment

@dataclass
class CharacterizationResult:
    """Standardized data structure for characterization experiment results."""
    qubit: int
    fit_successful: bool
    value: float
    unit: str
    stderr: float
    fit_parameters: Dict[str, Any]
    sweep_points: np.ndarray
    probabilities: np.ndarray
    raw_counts: List[Dict[str, int]]

class _BaseCharacterizationExperiment(BaseExperiment):
    """
    An abstract base class for characterization experiments like T1 and T2.

    This class provides a standardized workflow for experiments that involve
    sweeping a parameter (e.g., delay time), running circuits, and fitting the
    results to a physical model.
    """
    def __init__(self, qubit: int, sweep_points: List[float], unit: str = 's'):
        self.qubit = qubit
        self.sweep_points = np.array(sweep_points)
        self.unit = unit

    @abstractmethod
    def _create_circuits(self) -> List[QuantumCircuit]:
        """(Subclass implementation) Generates circuits for each sweep point."""
        pass

    @abstractmethod
    def _get_fit_function(self) -> Callable:
        """(Subclass implementation) Returns the function to fit the data to."""
        pass

    @abstractmethod
    def _get_initial_guess(self, x_data: np.ndarray, y_data: np.ndarray) -> List[float]:
        """(Subclass implementation) Provides an initial guess for the curve fit."""
        pass
    
    @abstractmethod
    def _get_result_from_fit_params(self, popt: List[float], perr: List[float]) -> Tuple[float, float]:
        """(Subclass implementation) Extracts the primary value and error from fit results."""
        pass

    def _process_results(self, results: List[Tuple[Any, Dict[str, int]]]) -> Tuple[np.ndarray, List[Dict[str, int]]]:
        """Processes raw counts into survival probabilities (P(|1>))."""
        probabilities = []
        counts_list = []
        for _, counts in results:
            total_shots = sum(counts.values())
            p1 = counts.get('1', 0) / total_shots if total_shots > 0 else 0.5
            probabilities.append(p1)
            counts_list.append(counts)
        return np.array(probabilities), counts_list

    def run_and_fit(self,
                    backend: BaseBackend,
                    shots: int = 1024,
                    plot_results: bool = True,
                    verbose: bool = False) -> CharacterizationResult:
        """
        Executes the full characterization: runs circuits, fits the decay, and optionally plots.
        """
        if verbose:
            print(f"--- Running {self.__class__.__name__} for qubit {self.qubit} ---")

        # 1. Generate and run circuits
        circuits = self._create_circuits()
        if verbose:
            print(f"  Generated {len(circuits)} circuits. Running on backend...")
        results = [backend.run(c, shots=shots) for c in circuits]
        
        # 2. Process data
        probabilities, raw_counts = self._process_results(results)
        
        # 3. Fit data
        fit_func = self._get_fit_function()
        initial_guess = self._get_initial_guess(self.sweep_points, probabilities)
        
        try:
            popt, pcov = curve_fit(fit_func, self.sweep_points, probabilities, p0=initial_guess, maxfev=10000)
            perr = np.sqrt(np.diag(pcov))
            fit_successful = True
            value, stderr = self._get_result_from_fit_params(popt, perr)
            if verbose:
                print(f"  Fit successful. Result: {value:.4e} {self.unit}")
        except RuntimeError:
            if verbose:
                print("  Curve fitting failed. Could not find optimal parameters.")
            popt, perr = ([np.nan] * len(initial_guess)), ([np.nan] * len(initial_guess))
            fit_successful = False
            value, stderr = np.nan, np.nan

        # 4. Package and return results
        result_obj = CharacterizationResult(
            qubit=self.qubit,
            fit_successful=fit_successful,
            value=value,
            unit=self.unit,
            stderr=stderr,
            fit_parameters=dict(zip(['popt', 'perr'], [popt, perr])),
            sweep_points=self.sweep_points,
            probabilities=probabilities,
            raw_counts=raw_counts
        )

        # 5. Plotting
        if plot_results:
            self._plot_data(result_obj)

        return result_obj

    def _plot_data(self, result: CharacterizationResult):
        """Helper function to plot the data and the fit."""
        fig, ax = plt.subplots()
        
        # Plot data points
        ax.plot(result.sweep_points, result.probabilities, 'o', label='Data')

        # Plot fit curve
        if result.fit_successful:
            fit_func = self._get_fit_function()
            fine_x = np.linspace(min(result.sweep_points), max(result.sweep_points), 200)
            ax.plot(fine_x, fit_func(fine_x, *result.fit_parameters['popt']), '-', 
                    label=f'Fit: {result.value:.2e} {result.unit}')
        
        ax.set_xlabel(f"Delay ({self.unit})")
        ax.set_ylabel("Excited State Probability P(|1>)")
        ax.set_title(f"{self.__class__.__name__} for Qubit {self.qubit}")
        ax.legend()
        plt.show()