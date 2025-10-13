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

EGM's architecture is engineered for modularity, flexibility, and extensibility. It is built upon a collection of distinct, high-cohesion components that work in concert to deliver powerful benchmarking capabilities.

*   **`experiments`**: The heart of EGM. This core module contains the "blueprints" for all benchmarking and characterization protocols, meticulously organized into a three-layer evaluation hierarchy.
*   **`analysis`**: A dedicated suite of tools for post-processing experimental data. It handles everything from raw data aggregation and statistical analysis to sophisticated model fitting and the extraction of key performance metrics.
*   **`engine`**: The core execution engine that orchestrates the entire experimental workflow. It manages circuit generation, submission to the backend, data retrieval, and coordination with the `analysis` module.
*   **`backends`**: A hardware abstraction layer that makes EGM hardware-agnostic. It provides a standardized interface for communicating with diverse quantum hardware platforms (cloud or on-premise) and simulators.
*   **`circuits`**: A foundational module for quantum circuit representation, construction, and manipulation, providing the essential objects that `experiments` and the `engine` operate on.
*   **`pulse`**: An interface for defining pulse-level experiments, enabling direct interaction with control hardware for low-level device physics characterization (e.g., Rabi, Ramsey, T1/T2).

---

### In-depth Look: The `experiments` Module's Three-Layer Hierarchy

The true power of EGM's design is revealed in the logical structure of the `experiments` module. It is organized into a three-layer hierarchy, allowing users to probe quantum processor performance at different levels of abstraction—from fundamental physics to application-level utility.

#### **Layer 1: `benchmarking` — Protocol-Level Benchmarking**

This layer answers the question: **"How good are the fundamental operations (gates and circuits)?"** It contains standardized, scalable protocols that yield critical fidelity metrics.

*   **Randomized Benchmarking (`rb`)**: Implements Standard, Interleaved, and other variants of RB to measure the average error rate of Clifford gates (Error Per Clifford, EPC) and, by extension, the fidelity of specific target gates (Error Per Gate, EPG).
*   **Cross-Entropy Benchmarking (`xeb`)**: Assesses the fidelity of quantum circuits by comparing their output distribution to that of a noiseless simulation, providing a holistic measure of performance on random circuits.
*   **Quantum Volume (`qv`)**: A full-stack benchmark that measures the largest "square" random circuit a quantum computer can successfully execute, reflecting a combined measure of qubit count, fidelity, and connectivity.

#### **Layer 2: `characterization` — Physics-Level Characterization**

This layer answers the question: **"What are the specific physical error sources and their magnitudes?"** It provides a suite of targeted experiments to diagnose noise mechanisms and validate quantum states.

*   **Coherent Errors (`coherent`)**: Quantifies unitary errors, such as systematic over/under-rotations. Experiments like **Rabi** and **Ramsey** are used to precisely measure pulse amplitude errors and qubit frequency detuning, which are primary sources of coherent gate infidelity.
*   **Incoherent Errors (`incoherent`)**: Measures stochastic noise sources, including energy relaxation time (**T1**) and dephasing time (**T2**), which are fundamental limits on quantum computation.
*   **Crosstalk (`crosstalk`)**: Characterizes the magnitude of unwanted interactions between qubits. This is crucial for assessing the viability of parallel gate operations and understanding the scalability limits of the processor.
*   **SPAM Errors (`spam`)**: Characterizes the fidelity of **S**tate **P**reparation **a**nd **M**easurement, a critical source of error that affects every quantum algorithm.
*   **Entanglement (`entanglement`)**: A specialized suite to verify the creation of high-fidelity multi-qubit entangled states, the essential resource for quantum advantage. This includes fidelity checks for:
    *   **Bell States**: The fundamental unit of two-qubit entanglement.
    *   **GHZ & W States**: Canonical examples of multi-qubit entanglement with distinct properties.
    *   **Graph & Cluster States**: The resource for measurement-based quantum computing and a key component in many quantum error correction codes.
*   **Tomography (`tomography`)**: Provides tools for full quantum state and process reconstruction.
    *   **State Tomography**: Validates the creation of specific quantum states by reconstructing their density matrices.
    *   **Process Tomography**: Characterizes the complete action of a quantum gate or process.

#### **Layer 3: `algorithmic` — Application-Level Benchmarking**

This layer answers the ultimate question: **"How well does the processor perform on end-to-end quantum algorithms?"** It assesses the practical performance of the system on small-scale but complete algorithms.

*   **Variational Algorithms (`variational`)**: Benchmarks the performance of hybrid quantum-classical algorithms like the **Variational Quantum Eigensolver (VQE)** and the **Quantum Approximate Optimization Algorithm (QAOA)**.
*   **Algebraic & Search Algorithms (`algebraic`)**: Assesses performance on foundational algorithms like **Grover's Search** and **Quantum Phase Estimation (QPE)**.
*   **Quantum Simulation (`simulation`)**: Evaluates the ability of the device to simulate other quantum systems, a primary proposed application for quantum computers.
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
# The `run` method is a high-level wrapper that handles circuit generation,
# execution on the backend, data processing, and model fitting.
print("\n" + "="*20, "Running 2-Qubit IRB for 'CNOT'", "="*20)
int_results_cnot = int_rb_cnot.run(backend, verbose=True, plot=True)

# 4. Get Results:
# Extract the calculated gate error from the results object.
gate_error = int_results_cnot.get('gate_error', -1)
print(f"\n[Final Result] Estimated Error of 'CNOT' gate = {gate_error:.3e}")

# Expected Output：
# ============================================================
#       Interleaved Randomized Benchmarking (IRB) Demonstration
# ============================================================
# [Setup] Using a simulated backend with:
#   - Per-gate depolarizing error: 1.5%
#   - SPAM error: 0.01%
#
#
# ==================== Running 2-Qubit IRB for 'CNOT' ====================
# [Step 1/3] Running Standard RB reference experiment...
# --- Running Standard 2-Qubit RB ---
# Generating 150 circuits for Standard RB...
# Fitting standard RB data...
# Fit successful. EPC = 2.763e-02
#
# [Step 2/3] Running Interleaved RB experiment with 'cnot'...
# Generating 150 circuits for Interleaved RB...
# Fitting interleaved RB data...
# Fit successful. Interleaved EPC = 3.864e-02
#
# [Step 3/3] Analyzing results and calculating EPG...
#
# --- Results ---
# Calculated Error of gate 'cnot' (EPG) = 1.104e-02
# Generating comparison plot...
#
# [Final Result] Estimated Error of 'CNOT' gate = 1.104e-02
# (Note: A plot showing the exponential decay curves will be displayed in a separate window if run in a graphical environment.)

```
## 6. Directory Structure

The project is organized to separate the core library, tests, examples, and documentation, ensuring a clean and maintainable codebase.

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
    ├── analysis/                  # Module: Data processing, fitting, and plotting
    ├── backends/                  # Module: Interfaces for quantum hardware & simulators
    ├── circuits/                  # Module: Quantum circuit construction & manipulation
    ├── engine/                    # Module: Core experiment orchestration engine
    │
    └── experiments/               # Module: Definitions of all experiment "blueprints"
        ├── base.py                # Abstract base class for all experiments
        │
        ├── benchmarking/          # Layer 1: Protocol-Level Benchmarking
        │   ├── rb.py              # e.g., Randomized Benchmarking
        │   ├── xeb.py             # e.g., Cross-Entropy Benchmarking
        │   └── ...
        │
        ├── characterization/      # Layer 2: Physics-Level Characterization
        │   ├── coherent/          # Coherent error experiments (e.g., Rabi, Ramsey)
        │   ├── crosstalk/         # Crosstalk measurement protocols
        │   ├── entanglement/      # Entangled state fidelity validation (e.g., Bell, GHZ)
        │   ├── incoherent/        # Incoherent error experiments (e.g., T1, T2)
        │   ├── spam/              # State Preparation and Measurement (SPAM) errors
        │   └── tomography/        # State and process tomography
        │
        └── algorithmic/           # Layer 3: Application-Level Benchmarking
            ├── variational/       # e.g., VQE, QAOA benchmarks
            ├── algebraic/         # e.g., Grover's Search, QPE benchmarks
            └── simulation/        # e.g., Quantum dynamics simulation benchmarks
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
