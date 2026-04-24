# # errorgnomark/errorgnomark/__init__.py

# """
# ErrorGnoMark: A Quantum Error Characterization and Benchmarking Toolkit.

# This is the main entry point of the ErrorGnoMark library.
# It exposes the most commonly used classes, functions, and objects
# for a streamlined user experience.
# """

# # 1. Define package metadata.
# # This is crucial for versioning, debugging, and user support.
# __version__ = "2.0.0"
# __author__ = "Xudan Chai"
# __email__ = "chaixd@baqis.ac.cn"


# # 2. Import from the high-level API module using absolute paths.
# # The import path starts from the top-level package name 'errorgnomark'.
# from egm.api import (
#     run_randomized_benchmarking,
#     run_t1_experiment,
#     run_process_tomography,
# )

# # 3. Expose key classes and functions from core modules using absolute paths.

# # From the 'circuits' module
# from egm.core.circuits.circuit import QuantumCircuit

# # --- Benchmarking Experiments ---
# from egm.experiments.benchmarking.rb import StandardRBExperiment, InterleavedRBExperiment
# from egm.experiments.benchmarking.xeb import StandardXEBExperiment, InterleavedXEBExperiment
# from egm.experiments.benchmarking.spb import SPBExperiment,InterleavedSPBExperiment
# from egm.experiments.benchmarking.prb import StandardPRBExperiment, InterleavedPRBExperiment


# # --- Characterization Experiments ---

# # Coherent Errors
# from egm.experiments.characterization.coherent.rabi_experiment import RabiExperiment
# from egm.experiments.characterization.coherent.ramsey_phase_experiment import RamseyPhaseExperiment

# # Crosstalk Errors
# from egm.experiments.characterization.crosstalk.simultaneous_rb_experiment import SimultaneousRBExperiment

# # Entanglement Fidelity
# from egm.experiments.characterization.entanglement.bell_state_fidelity import BellStateFidelity
# from egm.experiments.characterization.entanglement.ghz_state_fidelity import GHZStateFidelity
# from egm.experiments.characterization.entanglement.graph_state_fidelity import GraphStateFidelity
# from egm.experiments.characterization.entanglement.grid_cluster_state_fidelity import GridClusterStateFidelity
# from egm.experiments.characterization.entanglement.linear_cluster_state_fidelity import LinearClusterStateFidelity
# from egm.experiments.characterization.entanglement.w_state_fidelity import WStateFidelity

# # Incoherent Errors
# from egm.experiments.characterization.incoherent.leakage_rb_experiment import LeakageRBExperiment
# from egm.experiments.characterization.incoherent.pauli_twirling_experiment import PauliTwirlingExperiment
# from egm.experiments.characterization.incoherent.t1_experiment import T1Experiment
# from egm.experiments.characterization.incoherent.t2_echo_experiment import T2EchoExperiment
# from egm.experiments.characterization.incoherent.t2_ramsey_experiment import T2RamseyExperiment


# # --- SPAM (State Preparation and Measurement) Experiments ---
# from egm.experiments.spam.spam_characterization import SPAMCharacterization


# # --- Tomography Experiments ---
# from egm.experiments.tomography.process_tomography import ProcessTomography


# # 4. Define the public API of the package with `__all__`.
# # This list explicitly declares which names are intended for public use,
# # controlling `from egm import *` and aiding static analysis tools.
# __all__ = [
#     # Metadata
#     "__version__",
#     "__author__",
#     "__email__",

#     # High-level API functions
#     "run_randomized_benchmarking",
#     "run_t1_experiment",
#     "run_process_tomography",

#     # Core classes
#     "QuantumCircuit",

#     # Benchmarking Experiments
#     "StandardRBExperiment",
#     "InterleavedRBExperiment",
#     "StandardXEBExperiment",
#     "InterleavedXEBExperiment",
#     "SPBExperiment",
#     "InterleavedSPBExperiment",
#     "StandardPRBExperiment",
#     "InterleavedPRBExperiment",

#     # Characterization Experiments
#     "RabiExperiment",
#     "RamseyPhaseExperiment",
#     "SimultaneousRBExperiment",
#     "BellStateFidelity",
#     "GHZStateFidelity",
#     "GraphStateFidelity",
#     "GridClusterStateFidelity",
#     "LinearClusterStateFidelity",
#     "WStateFidelity",
#     "LeakageRBExperiment",
#     "PauliTwirlingExperiment",
#     "T1Experiment",
#     "T2EchoExperiment",
#     "T2RamseyExperiment",

#     # SPAM Experiments
#     "SPAMCharacterization",

#     # Tomography Experiments
#     "ProcessTomography",
# ]