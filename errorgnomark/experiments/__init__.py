# errorgnomark/experiments/__init__.py

"""
ErrorGnoMark Experiments Package

This is the top-level package for all quantum experiment protocols supported
by the framework. It provides the base class for all experiments and organizes
different experiment types into logical sub-packages.

The `BaseExperiment` class should be inherited by all concrete experiment classes.

Sub-packages:
- applications: High-level algorithms and applications.
- benchmarking: Protocols for benchmarking overall device performance (e.g., RB).
- characterization: Protocols for characterizing specific error sources (T1, T2, etc.).
- entanglement_verification: Protocols to verify the generation of entangled states.

Usage:
    from errorgnomark.experiments import BaseExperiment
    from errorgnomark.experiments.characterization.incoherent import T1Experiment
"""

# Import the base class for all experiments to make it easily accessible.
from .base_experiment import BaseExperiment

__all__ = [
    "BaseExperiment"
]