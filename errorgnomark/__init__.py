# errorgnomark/errorgnomark/__init__.py

"""
ErrorGnoMark: A Quantum Error Characterization and Benchmarking Toolkit.

This is the main entry point of the ErrorGnoMark library.
It exposes the most commonly used classes, functions, and objects
for a streamlined user experience.
"""

# 1. Define package metadata.
# This is crucial for versioning, debugging, and user support.
__version__ = "2.0.0"
__author__ = "Xudan Chai"
__email__ = "chaixd@baqis.ac.cn"


# 2. Import from the high-level API module using absolute paths.
# The import path starts from the top-level package name 'errorgnomark'.
from errorgnomark.api import (
    run_randomized_benchmarking,
    run_t1_experiment,
    run_process_tomography,
)

# 3. Expose key classes and functions from core modules using absolute paths.

# From the 'circuits' module
from errorgnomark.circuits.circuit import QuantumCircuit

# --- Benchmarking Experiments ---
from errorgnomark.experiments.benchmarking.rb import StandardRBExperiment, InterleavedRBExperiment
from errorgnomark.experiments.benchmarking.xeb import StandardXEBExperiment, InterleavedXEBExperiment
from errorgnomark.experiments.benchmarking.spb import SPBExperiment,InterleavedSPBExperiment
from errorgnomark.experiments.benchmarking.prb import StandardPRBExperiment, InterleavedPRBExperiment


# --- Characterization Experiments ---

# Coherent Errors
from errorgnomark.experiments.characterization.coherent.rabi_experiment import RabiExperiment
from errorgnomark.experiments.characterization.coherent.ramsey_phase_experiment import RamseyPhaseExperiment

# Crosstalk Errors
from errorgnomark.experiments.characterization.crosstalk.simultaneous_rb_experiment import SimultaneousRBExperiment

# Entanglement Fidelity
from errorgnomark.experiments.characterization.entanglement.bell_state_fidelity import BellStateFidelity
from errorgnomark.experiments.characterization.entanglement.ghz_state_fidelity import GHZStateFidelity
from errorgnomark.experiments.characterization.entanglement.graph_state_fidelity import GraphStateFidelity
from errorgnomark.experiments.characterization.entanglement.grid_cluster_state_fidelity import GridClusterStateFidelity
from errorgnomark.experiments.characterization.entanglement.linear_cluster_state_fidelity import LinearClusterStateFidelity
from errorgnomark.experiments.characterization.entanglement.w_state_fidelity import WStateFidelity

# Incoherent Errors
from errorgnomark.experiments.characterization.incoherent.leakage_rb_experiment import LeakageRBExperiment
from errorgnomark.experiments.characterization.incoherent.pauli_twirling_experiment import PauliTwirlingExperiment
from errorgnomark.experiments.characterization.incoherent.t1_experiment import T1Experiment
from errorgnomark.experiments.characterization.incoherent.t2_echo_experiment import T2EchoExperiment
from errorgnomark.experiments.characterization.incoherent.t2_ramsey_experiment import T2RamseyExperiment


# --- SPAM (State Preparation and Measurement) Experiments ---
from errorgnomark.experiments.spam.spam_characterization import SPAMCharacterization


# --- Tomography Experiments ---
from errorgnomark.experiments.tomography.process_tomography import ProcessTomography


# 4. Define the public API of the package with `__all__`.
# This list explicitly declares which names are intended for public use,
# controlling `from errorgnomark import *` and aiding static analysis tools.
__all__ = [
    # Metadata
    "__version__",
    "__author__",
    "__email__",

    # High-level API functions
    "run_randomized_benchmarking",
    "run_t1_experiment",
    "run_process_tomography",

    # Core classes
    "QuantumCircuit",

    # Benchmarking Experiments
    "StandardRBExperiment",
    "InterleavedRBExperiment",
    "StandardXEBExperiment",
    "InterleavedXEBExperiment",
    "SPBExperiment",
    "InterleavedSPBExperiment",
    "StandardPRBExperiment",
    "InterleavedPRBExperiment",

    # Characterization Experiments
    "RabiExperiment",
    "RamseyPhaseExperiment",
    "SimultaneousRBExperiment",
    "BellStateFidelity",
    "GHZStateFidelity",
    "GraphStateFidelity",
    "GridClusterStateFidelity",
    "LinearClusterStateFidelity",
    "WStateFidelity",
    "LeakageRBExperiment",
    "PauliTwirlingExperiment",
    "T1Experiment",
    "T2EchoExperiment",
    "T2RamseyExperiment",

    # SPAM Experiments
    "SPAMCharacterization",

    # Tomography Experiments
    "ProcessTomography",
]