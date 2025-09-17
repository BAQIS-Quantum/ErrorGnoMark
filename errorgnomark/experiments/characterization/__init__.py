# errorgnomark/experiments/characterization/__init__.py

"""
Quantum Device Characterization Experiments Package

This package contains experiment classes for characterizing quantum devices,
organized by the physical source of noise they target.

Sub-packages:
- spam: State Preparation and Measurement (SPAM) error characterization.
- incoherent: Experiments for T1, T2*, T2, and stochastic Pauli errors.
- coherent: Experiments for systematic errors like over-rotations and phase errors.
- leakage: Experiments to detect population leaving the computational subspace.
- crosstalk: Experiments to quantify interactions between concurrently operated qubits.
- tomography: High-precision, resource-intensive state and process tomography protocols.
"""

# This file is intentionally kept clean to encourage importing from sub-packages directly,
# e.g., from errorgnomark.experiments.characterization.incoherent import T1Experiment