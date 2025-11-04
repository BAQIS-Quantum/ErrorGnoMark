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
*   **`api`**: A high-level, user-friendly API that simplifies access to EGM's most common functionalities, making it easy to run standard benchmarks with just a few lines of code.

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

We recommend using a Python virtual environment for installation to avoid dependency conflicts.

#### 4.1. Standard Installation (from PyPI)

For general use, you can install the latest stable version directly from the Python Package Index (PyPI):
```bash
pip install errorgnomark
```

#### 4.2. Local Development Installation

If you plan to contribute to EGM or need the latest features not yet released on PyPI, you should install it from a local clone of the Gitee repository.

1.  **Clone the Repository from Gitee**

    First, clone the repository to your local machine.
    ```bash
    git clone https://gitee.com/xdchai/errorgnomark.git
    cd errorgnomark
    ```
    > **Note for Contributors:** If you plan to contribute code, please fork the repository on Gitee first. Then, clone your own fork using your personal URL (e.g., `git clone https://gitee.com/your-username/errorgnomark.git`).

2.  **Install in Editable Mode**

    The `-e` flag (for "editable") creates a symbolic link to the source code. This ensures that any changes you make to the code are immediately effective in your environment without needing to reinstall the package.
    ```bash
    pip install -e .
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
Here is a detailed breakdown of the project structure, illustrating the layered architecture and the role of each component.


errorgnomark/
├── .gitignore                     # Git ignore configuration
├── LICENSE                        # Project license
├── README.md                      # Project overview and guide
├── pyproject.toml                 # Project config, dependencies, and build settings
├── docs/                          # Project documentation
├── examples/                      # Example code and notebooks
├── tests/                         # Unit and integration tests
└── errorgnomark/                  # Core source code package
    ├── __init__.py                # Package initializer, exposes public API
    ├── api.py                     # High-level, user-facing API
    ├── analysis/                  # Data analysis and post-processing
    │   ├── rb.py                  # Randomized Benchmarking (RB) analysis
    │   ├── tomography.py          # Tomography data processing
    │   ├── reporting.py           # Report generation tools
    │   └── ...                    # Other analysis scripts (XEB, SPB, etc.)
    ├── backends/                  # Hardware and simulator backends
    │   ├── base_backend.py        # Base class for all backends
    │   ├── ideal_backend.py       # Ideal, noiseless simulator
    │   ├── quafu_cloud.py         # Quafu cloud platform backend
    │   └── ...
    ├── circuits/                  # Circuit construction, compilation & visualization
    │   ├── circuit.py             # Core circuit object definition
    │   ├── gate_sets.py           # Gate sets and transpilation
    │   ├── operations.py          # Quantum gate and operation definitions
    │   └── visualization.py       # Circuit visualization tools
    ├── datastore/                 # Data storage and retrieval
    │   ├── models.py              # Data models for results
    │   └── storage/               # Pluggable storage drivers (HDF5, JSON)
    ├── diagnostics/               # High-level diagnostic tools
    │   ├── crosstalk_analyzer.py  # Crosstalk analysis
    │   ├── error_budget_analyzer.py # Error budget analysis
    │   └── health_assessor.py     # System health assessment
    ├── engine/                    # Experiment execution engine
    │   └── executor.py            # Schedules and runs experiment tasks
    ├── experiments/               # Experiment protocol definitions
    │   ├── base.py                # Base class for all experiments
    │   ├── benchmarking/          # Protocol-Level Benchmarking
    │   │   ├── rb.py              # Randomized Benchmarking (RB)
    │   │   ├── xeb.py             # Cross-Entropy Benchmarking (XEB)
    │   │   ├── qv.py              # Quantum Volume (QV)
    │   │   └── ...                # Other protocols (MRB, PRB, SPB)
    │   └── characterization/      # Physics-Level Characterization
    │       ├── coherent/          # Coherent errors (Rabi, Ramsey)
    │       ├── crosstalk/         # Crosstalk measurement
    │       ├── incoherent/        # Incoherent errors (T1, T2)
    │       ├── spam/              # State Prep & Measurement (SPAM) errors
    │       └── tomography/        # State and Process Tomography
    ├── simulators/                # Classical circuit simulators
    │   └── statevector_simulator.py # Statevector-based simulator
    └── workflows/                 # High-level experiment workflows
        ├── base.py                # Base class for all workflows
        ├── parameter_strategies.py  # Parameter sweeping strategies
        ├── preset_protocols.py    # Pre-configured experiment protocols
        └── schemas.py             # Data schemas for workflow I/O
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
