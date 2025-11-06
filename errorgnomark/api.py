# errorgnomark/api.py

"""
High-Level User-Facing API for ErrorGnoMark.

This module provides a set of simplified, high-level functions for running common
benchmarking and characterization experiments. The goal of this API is to abstract
away the underlying 'Experiment' objects and execution details, allowing users to
get results with a single function call.

Each function in this module is designed to be a "one-shot" command for a specific
protocol. Users provide the target qubits and an execution engine, and the function
handles circuit generation, execution, data analysis, and plotting.
"""

# -------------------------------------------------------------------
# 1. Standard Library Imports
# -------------------------------------------------------------------
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

# -------------------------------------------------------------------
# 2. Third-Party Library Imports
# -------------------------------------------------------------------
# We import matplotlib.pyplot for type hinting axes, a common practice.
import matplotlib.pyplot as plt

# -------------------------------------------------------------------
# 3. Internal Framework Imports (errorgnomark)
# -------------------------------------------------------------------
# Import the necessary components that the API will orchestrate.
# These are the building blocks that our high-level functions will use.
from errorgnomark.circuits.circuit import Gate
from errorgnomark.engine.executor import QuantumEngine
from errorgnomark.experiments.benchmarking.rb import (
    DEFAULT_CIRCUITS_PER_DEPTH as RB_CIRCUITS_PER_DEPTH,
    DEFAULT_RB_DEPTHS,
    InterleavedRBExperiment,
    StandardRBExperiment,
)
from errorgnomark.experiments.benchmarking.xeb import (
    DEFAULT_NATIVE_GATES as XEB_NATIVE_GATES,
    InterleavedXEBExperiment,
    StandardXEBExperiment,
)

# Configure logging for user feedback
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Define the public API of this module
__all__ = [
    "run_standard_rb",
    "run_interleaved_rb",
    "run_standard_xeb",
    "run_interleaved_xeb",
]


# ==============================================================================
# Randomized Benchmarking (RB) API Functions
# ==============================================================================

def run_standard_rb(
    qubits: Union[int, List[int]],
    engine: QuantumEngine,
    shots: int,
    depths: List[int] = DEFAULT_RB_DEPTHS,
    circuits_per_depth: int = RB_CIRCUITS_PER_DEPTH,
    seed: Optional[Union[int, float]] = None,
    plot: bool = True,
    axes: Optional[plt.Axes] = None,
    **kwargs: Any,
) -> Dict:
    """
    Runs a standard Randomized Benchmarking (RB) experiment.

    This high-level function instantiates a StandardRBExperiment, runs it on the
    provided engine, analyzes the results, and optionally plots the decay curve.

    Args:
        qubits: The qubit or list of qubits to benchmark.
        engine: The configured QuantumEngine to execute circuits on.
        shots: The number of times to execute each circuit.
        depths: A list of Clifford sequence depths for the experiment.
        circuits_per_depth: The number of random circuits to generate for each depth.
        seed: A seed for the random number generator to ensure reproducibility.
        plot: If True, generates and shows a plot of the RB decay curve.
        axes: A matplotlib Axes object to plot on. If None, a new figure is created.
        **kwargs: Additional keyword arguments to be passed to the StandardRBExperiment
                  constructor (e.g., `native_gates`, `clifford_factory`).

    Returns:
        A dictionary containing the analysis results, including the fit parameters
        and the calculated Error Per Clifford (EPC).
    """
    logging.info(f"API call: `run_standard_rb` on qubits {qubits}.")
    
    # 1. Instantiate the experiment object with user-provided parameters.
    rb_experiment = StandardRBExperiment(
        qubits=qubits,
        depths=depths,
        circuits_per_depth=circuits_per_depth,
        seed=seed,
        **kwargs,
    )

    # 2. Execute the experiment's run method, which handles the full workflow.
    results = rb_experiment.run(engine, shots=shots, plot=plot, axes=axes)

    # 3. Return the final analysis results.
    return results


def run_interleaved_rb(
    qubits: Union[int, List[int]],
    interleaved_gate: Gate,
    engine: QuantumEngine,
    shots: int,
    depths: List[int] = DEFAULT_RB_DEPTHS,
    circuits_per_depth: int = RB_CIRCUITS_PER_DEPTH,
    seed: Optional[Union[int, float]] = None,
    plot: bool = True,
    axes: Optional[plt.Axes] = None,
    **kwargs: Any,
) -> Optional[Dict]:
    """
    Runs an Interleaved Randomized Benchmarking (IRB) experiment.

    This function calculates the fidelity of a specific gate by comparing a
    standard RB experiment with one where the target gate is interleaved
    between each Clifford.

    Args:
        qubits: The qubit or list of qubits involved in the benchmark.
        interleaved_gate: The Gate object to be benchmarked.
        engine: The configured QuantumEngine to execute circuits on.
        shots: The number of times to execute each circuit.
        depths: A list of Clifford sequence depths for the experiment.
        circuits_per_depth: The number of random circuits to generate for each depth.
        seed: A seed for the random number generator to ensure reproducibility.
        plot: If True, generates a comparison plot of the two decay curves.
        axes: A matplotlib Axes object to plot on. If None, a new figure is created.
        **kwargs: Additional keyword arguments to be passed to the
                  InterleavedRBExperiment constructor (e.g., `native_gates`).

    Returns:
        A dictionary containing the analysis results, including the calculated
        Error Per Gate (EPG), and the results from both the standard and
        interleaved runs. Returns None if the reference experiment fails.
    """
    logging.info(f"API call: `run_interleaved_rb` for gate '{interleaved_gate.name}' on qubits {qubits}.")
    
    irb_experiment = InterleavedRBExperiment(
        qubits=qubits,
        interleaved_gate=interleaved_gate,
        depths=depths,
        circuits_per_depth=circuits_per_depth,
        seed=seed,
        **kwargs,
    )

    results = irb_experiment.run(engine, shots=shots, plot=plot, axes=axes)
    
    return results


# ==============================================================================
# Cross-Entropy Benchmarking (XEB) API Functions
# ==============================================================================

def run_standard_xeb(
    qubits: List[int],
    engine: QuantumEngine,
    shots: int = 2048,
    depths: List[int] = [0, 5, 10, 15, 25, 40, 60],
    circuits_per_depth: int = 30,
    plot: bool = True,
    axes: Optional[Tuple[plt.Axes, plt.Axes]] = None,
    seed: Optional[Union[int, float]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Runs a standard Cross-Entropy Benchmarking (XEB) experiment.

    This function generates random circuits, executes them on both an ideal
    simulator and a noisy backend, and then calculates and fits the XEB fidelity
    and Speckle Purity decay curves.

    Args:
        qubits: The list of qubits to benchmark.
        engine: The configured QuantumEngine to execute circuits on.
        shots: The number of times to execute each circuit.
        depths: A list of circuit depths for the experiment.
        circuits_per_depth: The number of random circuits to generate for each depth.
        plot: If True, generates plots of the XEB and SPB decay curves.
        axes: A tuple of two matplotlib Axes objects (for XEB and SPB) to plot on.
        seed: A seed for the random number generator to ensure reproducibility.
        **kwargs: Additional keyword arguments to be passed to the
                  StandardXEBExperiment constructor (e.g., `gate_set`, `topology`).

    Returns:
        A dictionary containing the full analysis results for both XEB and SPB.
    """
    logging.info(f"API call: `run_standard_xeb` on qubits {qubits}.")

    xeb_experiment = StandardXEBExperiment(
        qubits=qubits,
        depths=depths,
        circuits_per_depth=circuits_per_depth,
        seed=seed,
        native_gates=kwargs.pop('native_gates', XEB_NATIVE_GATES),
        **kwargs,
    )

    results = xeb_experiment.run(engine, shots=shots, plot=plot, axes=axes)

    return results


def run_interleaved_xeb(
    qubits: List[int],
    interleaved_gate: Gate,
    engine: QuantumEngine,
    shots: int = 2048,
    depths: List[int] = [0, 5, 10, 15, 25, 40, 60],
    circuits_per_depth: int = 30,
    plot: bool = True,
    axes: Optional[Tuple[plt.Axes, plt.Axes]] = None,
    seed: Optional[Union[int, float]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Runs an Interleaved Cross-Entropy Benchmarking (IXEB) experiment.

    This function calculates the fidelity of a specific gate by comparing a
    standard XEB experiment with one where the target gate is interleaved
    within the random circuits.

    Args:
        qubits: The list of qubits involved in the benchmark.
        interleaved_gate: The Gate object to be benchmarked.
        engine: The configured QuantumEngine to execute circuits on.
        shots: The number of times to execute each circuit.
        depths: A list of circuit depths for the experiment.
        circuits_per_depth: The number of random circuits to generate for each depth.
        plot: If True, generates comparison plots for XEB and SPB curves.
        axes: A tuple of two matplotlib Axes objects (for XEB and SPB) to plot on.
        seed: A seed for the random number generator to ensure reproducibility.
        **kwargs: Additional keyword arguments to be passed to the
                  InterleavedXEBExperiment constructor (e.g., `gate_set`).

    Returns:
        A dictionary containing the analysis results, including the calculated
        gate error, and the full results from both the standard and
        interleaved runs.
    """
    logging.info(f"API call: `run_interleaved_xeb` for gate '{interleaved_gate.name}' on qubits {qubits}.")

    ixeb_experiment = InterleavedXEBExperiment(
        qubits=qubits,
        interleaved_gate=interleaved_gate,
        depths=depths,
        circuits_per_depth=circuits_per_depth,
        seed=seed,
        native_gates=kwargs.pop('native_gates', XEB_NATIVE_GATES),
        **kwargs,
    )

    results = ixeb_experiment.run(engine, shots=shots, plot=plot, axes=axes)

    return results