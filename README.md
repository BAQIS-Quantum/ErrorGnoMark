# ErrorGnoMark: A Modular Software Suite for Quantum Benchmarking and Characterization

[![PyPI Version](https://img.shields.io/pypi/v/errorgnomark.svg?style=flat-square)](https://pypi.org/project/errorgnomark/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/BAQIS-Quantum/ErrorGnoMark/ci.yml?branch=main&style=flat-square)](https://github.com/BAQIS-Quantum/ErrorGnoMark/actions)
[![Python Version](https://img.shields.io/pypi/pyversions/errorgnomark.svg?style=flat-square)](https://pypi.org/project/errorgnomark/)
[![License](https://img.shields.io/github/license/BAQIS-Quantum/ErrorGnoMark.svg?style=flat-square)](https://github.com/BAQIS-Quantum/ErrorGnoMark/blob/main/LICENSE)
[![Code Coverage](https://img.shields.io/codecov/c/github/BAQIS-Quantum/ErrorGnoMark.svg?style=flat-square)](https://codecov.io/gh/BAQIS-Quantum/ErrorGnoMark)


## 1. Overview

ErrorGnoMark (EGM) is a comprehensive, modular software toolkit designed for the full-stack performance evaluation of quantum computing systems. It provides a powerful suite of tools for benchmarking and characterization, covering all layers of the quantum stack—from the underlying physical hardware to gates, circuits, and application-level performance. The name **ErrorGnoMark** itself encapsulates this core mission, combining **'error'** with the root **'gno'** (from *diagnose*, meaning to know or identify) and **'mark'** (from *benchmark*, meaning to measure or evaluate).

Built with modularity and component-based design at its core, EGM allows users to integrate it into their own systems for secondary development or to use its end-to-end capabilities for generating complete performance reports for quantum chips. These reports combine raw test data from various protocols with in-depth analysis, presenting a complete, clear, professional, and traceable evaluation result.

Built with modularity and component-based design at its core, EGM allows users to integrate it into their own systems for secondary development or to use its end-to-end capabilities for generating complete performance reports for quantum chips. These reports combine raw test data from various protocols with in-depth analysis, presenting a complete, clear, professional, and readable assessment for the user.

## 2. Potential Applications

EGM is designed to be a critical tool in various stages of the quantum computing development cycle:

*   **Quantum Chip Calibration:** Provides detailed feedback on gate and qubit performance to guide hardware calibration and optimization routines.
*   **Quantum Compilation Optimization:** Evaluates the performance impact of different compilation strategies by benchmarking the resulting quantum circuits.
*   **Cloud Platform Monitoring:** Enables real-time, continuous monitoring of quantum hardware performance on cloud platforms, ensuring users have an accurate and up-to-date understanding of device quality.

## 3. Key Modules & Components

EGM's architecture is built around several key components, ensuring flexibility and extensibility:

*   **`experiment`**: The central module for defining all benchmarking and characterization protocols.

*   **`analysis`**: A suite of tools for processing experimental data, fitting models, and extracting key performance metrics.
*   **`engine`**: The core execution engine that orchestrates experiments, from circuit generation to data acquisition and analysis.
*   **`backend`**: An abstraction layer for interfacing with different quantum hardware or simulators, essential for end-to-end workflows.
*   **`circuit`**: A utility module for circuit construction and manipulation, primarily used for end-to-end workflows.
*   **`pulse`**: An interface for defining pulse-level experiments, enabling direct interaction with control hardware for low-level characterization.
*   **`simulators`**: A collection of built-in, extensible simulators for testing and development.

---

<!-- ### In-depth Look: The `Experiment` Module -->

The **`experiment`** module is the heart of EGM and is divided into two main categories: 

#### 3.1. Benchmarking

This module includes a collection of state-of-the-art protocols for assessing gate and circuit fidelity:
*   **Randomized Benchmarking (RB)** and **Interleaved RB (IRB)**
*   **Cross-Entropy Benchmarking (XEB)**: Including multi-qubit fidelity estimation and fitting of single/two-qubit gate error rates.
*   **Channel Spectrum Benchmarking (CSB)**
*   **Mirror Randomized Benchmarking (MRB)**

#### 3.2. Characterization

This module provides a set of targeted experiments to diagnose specific noise mechanisms:
*   **Coherent Errors**: Quantify unitary errors like over/under-rotations.
*   **Incoherent Errors**: Measure stochastic noise sources like T1 and T2.
*   **Crosstalk**: Characterize unwanted interactions between qubits.
*   **Leakage**: Measure transitions to non-computational states.
*   **SPAM**: Characterize State Preparation and Measurement errors.
*   **Tomography**:
    *   **State Tomography**: For both arbitrary and graph states.
    *   **Process Tomography**
    *   **Gate Set Tomography (GST)**
---

## 4. Installation 
We recommend using a Python virtual environment for installation.

#### 4.1. Standard Installation (from PyPI)

For general use, you can install the latest stable version directly from the Python Package Index (PyPI):
```bash
pip install errorgnomark
```
#### 4.2. Local Development Installation

If you plan to contribute to EGM or need the latest features not yet released, install it from a local clone of the repository:


1. Clone the repository (replace with your fork's URL if contributing)
```bash
git clone https://github.com/your-org/errorgnomark.git
cd errorgnomark
```

2. Install in editable mode
The '-e' flag ensures that changes you make to the source code
are immediately effective without needing to reinstall.
```bash
pip install -e 
```

## 5. Usage

EGM supports both high-level, end-to-end workflows and granular control for custom experiments where users can define their own backends.

#### Example: End-to-End Interleaved RB

The following example demonstrates how to measure the error of a CNOT gate using 2-qubit Interleaved Randomized Benchmarking (IRB) with a built-in dummy backend.

```python
# Import necessary classes
import numpy as np
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.rb import InterleavedRBExperiment

# 1. Setup: Instantiate a simulated backend.
# Here, we define a backend with a 1.5% per-gate depolarizing error
# and a 0.01% SPAM (State Preparation and Measurement) error.
backend = DummyBackend(depolarizing_error=0.015, spam_error=0.0001)

print("="*60)
print("      Interleaved Randomized Benchmarking (IRB) Demonstration")
print("="*60)
print("[Setup] Using a simulated backend with:")
print(f"  - Per-gate depolarizing error: {backend.depolarizing_error:.1%}")
print(f"  - SPAM error: {backend.spam_error:.2%}\n")

# 2. Define the Experiment:
# Create an Interleaved RB experiment targeting the 'CNOT' gate on qubits [0, 1].
int_rb_cnot = InterleavedRBExperiment(qubits=[0, 1], target_gate_name='CNOT')

# 3. Run and Analyze:
# The `run_and_fit` method is a high-level wrapper that handles circuit generation,
# execution on the backend, data processing, and model fitting.
print("\n" + "="*20, "Running 2-Qubit IRB for 'CNOT'", "="*20)
int_results_cnot = int_rb_cnot.run_and_fit(backend, verbose=True, plot=True)

# 4. Get Results:
# Extract the calculated gate error from the results object.
gate_error = int_results_cnot.get('gate_error', -1)
print(f"\n[Final Result] Estimated Error of 'CNOT' gate = {gate_error:.3e}")

# Expected Output：
============================================================
      Interleaved Randomized Benchmarking (IRB) Demonstration
============================================================
[Setup] Using a simulated backend with:
  - Per-gate depolarizing error: 1.5%
  - SPAM error: 0.01%


==================== Running 2-Qubit IRB for 'CNOT' ====================
[Fit] Standard RB decay parameter (p_std) = 0.9632
[Fit] Interleaved RB decay parameter (p_int) = 0.9485
[Analysis] Error per Clifford (EPC) = 0.0276
[Analysis] Interleaved Error per Clifford (EPC_int) = 0.0386

[Final Result] Estimated Error of 'CNOT' gate = 1.104e-02
# (Note: A plot showing the exponential decay curves will be displayed in a separate window if run in a graphical environment.)
```
## 6. Directory Structure
The project is organized to separate the core library, tests, examples, and documentation.



```text
errorgnomark/
├── .gitignore                     # Git ignore file
├── LICENSE                        # Project license (e.g., Apache-2.0)
├── README.md                      # Project overview and user guide
├── pyproject.toml                 # Project metadata and dependency management
│
├── docs/                          # Documentation files (e.g., for Sphinx)
├── examples/                      # Example scripts and notebooks for users
├── tests/                         # Unit and integration tests for all modules
│
└── errorgnomark/                  # Core library source code
    ├── __init__.py                # Makes 'errorgnomark' a Python package
    ├── api.py                     # Public-facing, simplified API for common tasks
    │
    ├── analysis/                  # Module: General data analysis, fitting, and plotting
    │   ├── __init__.py
    │   ├── fitting.py             # Generic curve fitting models
    │   ├── plotting.py            # Standardized plotting utilities
    │   └── result.py              # Defines the standard ExperimentResult data structure
    │
    ├── backends/                  # Module: Interfaces for quantum backends
    │   ├── __init__.py
    │   ├── base.py                # Abstract base class for all backends
    │   ├── dummy_backend.py       # A simple simulator for testing purposes
    │   └── quafu_cloud.py         # Backend for the Quafu quantum cloud platform
    │
    ├── circuits/                  # Module: Quantum circuit construction and manipulation
    │   ├── __init__.py
    │   ├── circuit.py             # Core QuantumCircuit class definition
    │   ├── operations.py          # Definition of custom gates and operations
    │   └── ...
    │
    ├── engine/                    # Module: Core engine for experiment orchestration
    │   ├── __init__.py
    │   └── scheduler.py           # Manages experiment execution and data retrieval
    │
    └── experiments/               # Module: Definitions of all experiment "blueprints"
        ├── __init__.py
        ├── base.py                # Abstract base class for all experiments
        │
        ├── benchmarking/          # Protocols for benchmarking quantum device performance
        │   ├── __init__.py
        │   ├── rb.py              # e.g., Randomized Benchmarking (RB)
        │   ├── qv.py              # e.g., Quantum Volume
        │   └── ...
        │
        ├── characterization/      # Protocols for characterizing noise sources
        │   ├── __init__.py
        │   ├── coherent/          # Coherent error characterization (e.g., Ramsey)
        │   │   ├── rabi_experiment.py
        │   │   └── ...
        │   ├── incoherent/        # Incoherent error characterization (e.g., T1, T2)
        │   │   ├── t1_experiment.py
        │   │   ├── t2_echo_experiment.py
        │   │   └── ...
        │   ├── spam/              # State Preparation and Measurement (SPAM) error
        │   └── ...
        │
        └── tomography/            # Quantum State and Process Tomography
            ├── __init__.py
            ├── process_tomography/
            └── state_tomography/
```

## 7. Contributing
We welcome contributions from the community! If you'd like to contribute, please follow these steps:

* Fork the repository on GitHub.
* Clone your fork to your local machine.
* Create a new branch for your feature or bug fix (git checkout -b feature/your-feature-name).
* Make your changes, ensuring you add or update tests as appropriate.
* Update the documentation if you are adding new features.
* Push your branch to your fork and open a Pull Request to the main repository.

## 8. References
[1] The methods and principles implemented in Errorgnomark are based on cutting-edge research in quantum characterization, verification, and validation (QCVV).

[2] Wack, A., Paik, H., Javadi-Abhari, A., et al. Quality, Speed, and Scale: Three key attributes to measure the performance of near-term quantum computers. arXiv:2110.14108 (2021).
Klimov, P.V., Bengtsson, A., Quintana, C. et al. Optimizing quantum gates towards the scale of logical qubits. Nature Communications, 15, 2442 (2024). https://doi.org/10.1038/s41467-024-46623-y.

[3] Gu, Y., Zhuang, WF., Chai, X. et al. Benchmarking universal quantum gates via channel spectrum. Nature Communications, 14, 5880 (2023). https://doi.org/10.1038/s41467-023-41598-8.
