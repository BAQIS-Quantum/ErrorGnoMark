# File: egm/core/experiments/benchmarking/rb.py
# ---------------------------------------------------------------------
# Module: Randomized Benchmarking (RB) - Unified & Modular Architecture
# ---------------------------------------------------------------------
# Architecture Overview:
#
# Layer 1: Core Kernel (_generate_circuit)
#          - Pure mathematical logic (Clifford sequence generation).
#
# Layer 2: Single Wrappers (generate_single_...)
#          - Business logic separation (Standard vs Interleaved).
#          - Handles Physics INLINE (Decomposition).
#          - Returns physical/executable circuits.
#
# Layer 3: Batch & Orchestration (generate_..._circuits)
#          - Handles Batching, Topology (Merge/Remap).
#          - Handles Measurement Strategy.
# ---------------------------------------------------------------------

from __future__ import annotations
import random
import logging
from typing import List, Dict, Optional, Union, Tuple, Protocol, Any, Sequence

# Internal Framework Imports
from egm.foundation.circuits.circuit import QuantumCircuit, Gate
from egm.execution.executor import QuantumEngine
from egm.analysis.rb import stitch_rb_results, analyze_rb_standard, calculate_epg
from egm.foundation.circuits.gate_sets import CliffordGateSet
from egm.experiments.physical.benchmarking.tools.rb_tools import _is_measure_gate

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# ---------------------------------------------------------------------
# Default Configuration
# ---------------------------------------------------------------------
DEFAULT_RB_DEPTHS: List[int] = [0, 2, 4, 8, 16, 32, 64, 100]
DEFAULT_CIRCUITS_PER_DEPTH: int = 20


# ---------------------------------------------------------------------
# Protocols & Helpers
# ---------------------------------------------------------------------
class CliffordFactory(Protocol):
    """
    Protocol defining the interface for a Clifford gate sequence generator.
    """
    def get_random_clifford_and_inverse(
            self, qubits: List[int], seed: Optional[Union[int, float]]
    ) -> Tuple[List[Gate], List[Gate]]:
        ...


def remap_circuit_layer(circuit: QuantumCircuit, target_qubits: Sequence[int]) -> QuantumCircuit:
    """
    Maps a logical circuit template to specific target physical qubits.

    [Core Utility & Why we need it]
    -------------------------------
    Function: Spatial Translation ("Copy Paste + Change Address").
    Use Case: Essential for 'same_per_qubit' (Control Variable) experiments.
              It allows us to generate ONE template logic circuit (on qubit 0),
              and then map the exact same mathematical sequence to Qubit 1, Qubit 2, etc.

    [Design Note: Why use Sequence[int] instead of list[int]?]
    ----------------------------------------------------------
    1. Definition Scope: 'Sequence' is broader. It accepts both [0, 1] (list) and (0, 1) (tuple).
    2. Hashability: Tuples are hashable; lists are not. Using Sequence allows us to accept user input flexibly
       and convert to tuple internally for storage (e.g. as dictionary keys).

    Args:
        circuit: The source logical circuit (usually defined on abstract qubits like [0]).
        target_qubits: The physical qubits to map onto.

    Returns:
        A new QuantumCircuit instance with gates mapped to target_qubits.
    """
    src_qubits = sorted(list(circuit.qubits))
    dst_qubits = list(target_qubits)
    if len(src_qubits) != len(dst_qubits):
        raise ValueError(f"Remap dimension mismatch: {src_qubits} -> {dst_qubits}")

    mapping = dict(zip(src_qubits, dst_qubits))
    new_gates = []

    for g in circuit.gates:
        if _is_measure_gate(g): continue
        new_q_args = tuple(mapping.get(q, q) for q in g.qubits)
        new_gates.append(Gate(g.name, new_q_args, params=g.params))

    new_circuit = QuantumCircuit(qubits=sorted(dst_qubits), gates=new_gates)
    new_circuit.metadata = circuit.metadata.copy()
    new_circuit.metadata["remapped_from"] = src_qubits
    return new_circuit


def merge_circuits_layer(circuits_list: List[QuantumCircuit]) -> QuantumCircuit:
    """
    Merges multiple disjoint logical circuits into one simultaneous circuit.

    [Core Utility & Why we need it]
    -------------------------------
    Function: Parallel Composition ("Jigsaw Puzzle").
    Use Case: Essential for 'Simultaneous RB'. Stitch distinct circuit objects
              into a single global circuit object before execution.

    Args:
        circuits_list: A list of independent QuantumCircuit objects.

    Returns:
        A single merged QuantumCircuit containing all gates from input circuits.
    """
    all_qubits = set()
    all_gates = []
    meta_depth = None

    for qc in circuits_list:
        all_qubits.update(qc.qubits)
        all_gates.extend(qc.gates)
        if meta_depth is None: meta_depth = qc.metadata.get("depth")

    merged_qc = QuantumCircuit(qubits=sorted(list(all_qubits)), gates=all_gates)
    merged_qc.metadata = {"depth": meta_depth, "mode": "simultaneous_merged"}
    return merged_qc


# =============================================================================
# Level 1: Core Kernel (Pure Logic)
# =============================================================================

def _generate_circuit(
        qubits: Sequence[int],
        depth: int,
        seed: Optional[Union[int, float]] = None,
        clifford_factory: Optional[CliffordFactory] = None,
        interleaved_gate: Optional[Gate] = None,
) -> QuantumCircuit:
    """
    Internal kernel to generate a single Clifford sequence circuit of a given depth.
    Responsibilities: Pure math (Clifford group sampling).
    """
    if clifford_factory is None:
        clifford_factory = CliffordGateSet()

    rng = random.Random(seed)
    q_list = list(qubits)
    circ = QuantumCircuit(qubits=q_list)

    if depth == 0:
        circ.metadata.update({"depth": 0, "gate_count": 0, "seed": seed})
        return circ

    inv_seq = []

    # Forward sequence generation
    for _ in range(depth):
        fwd, inv = clifford_factory.get_random_clifford_and_inverse(
            q_list, seed=rng.random()
        )
        circ.add_gates(fwd)
        if interleaved_gate:
            circ.add_gate(interleaved_gate)
        inv_seq.append(inv)

    # Inverse sequence appending
    for invs in reversed(inv_seq):
        circ.add_gates(invs)

    circ.metadata.update({
        "depth": depth,
        "gate_count": len(circ.gates),
        "seed": seed
    })

    return circ


# =============================================================================
# Level 2: Single Wrappers (Business Logic + Physics Encapsulation)
# =============================================================================

def generate_single_standard_rb_circuit(
        qubits: Sequence[int],
        depth: int,
        seed: Optional[Union[int, float]] = None,
        clifford_factory: Optional[CliffordFactory] = None,
        native_gates: Optional[Union[List[str], str]] = None,
) -> QuantumCircuit:
    """Wrapper for Standard RB: Returns a single DECOMPOSED circuit."""
    circ = _generate_circuit(
        qubits=qubits,
        depth=depth,
        seed=seed,
        clifford_factory=clifford_factory,
        interleaved_gate=None
    )
    # [Logic]: Physical decomposition is encapsulated here
    if native_gates:
        circ = circ.decompose(basis_gates=native_gates)
    return circ


def generate_single_interleaved_rb_circuit(
        qubits: Sequence[int],
        depth: int,
        interleaved_gate: Gate,
        seed: Optional[Union[int, float]] = None,
        clifford_factory: Optional[CliffordFactory] = None,
        native_gates: Optional[Union[List[str], str]] = None,
) -> QuantumCircuit:
    """Wrapper for Interleaved RB: Returns a single DECOMPOSED circuit."""
    if interleaved_gate is None:
        raise ValueError("Interleaved RB requires a valid 'interleaved_gate'.")

    circ = _generate_circuit(
        qubits=qubits,
        depth=depth,
        seed=seed,
        clifford_factory=clifford_factory,
        interleaved_gate=interleaved_gate
    )
    # [Logic]: Physical decomposition is encapsulated here
    if native_gates:
        circ = circ.decompose(basis_gates=native_gates)
    return circ


# =============================================================================
# Level 3: Batch & Orchestration
# =============================================================================

# -------------------
# A. Standard RB Family
# -------------------

def generate_standard_rb_circuits(
        qubits: Sequence[int],
        depths: List[int],
        circuits_per_depth: int,
        seed: Optional[int] = None,
        native_gates: Optional[Union[List[str], str]] = None,
        clifford_factory: Optional[CliffordFactory] = None,
        with_measurement: bool = True
) -> List[QuantumCircuit]:
    """
    Generates a batch of Standard RB circuits.

    [Design Note: Seed Propagation & Reproducibility]
    -------------------------------------------------
    1. Master Seed Mode: The user provides a single 'seed' (e.g., 42) at this top level.
    2. Derivation Mechanism: We create `rng = random.Random(seed)`. Inside the loop,
       we generate a derived seed using `c_seed = rng.random()` for each circuit.

    Q: If I run this function twice with seed=42, will Circuit A (Run 1) be identical to Circuit A (Run 2)?
    A: YES. The 'rng' will produce the exact same sequence of derived seeds every time.
       This ensures FULL REPRODUCIBILITY across experiments.

    Q: Will Circuit A and Circuit B in the same batch look the same?
    A: NO. Circuit A gets the 1st number from the RNG, Circuit B gets the 2nd.
       They are distinct, ensuring statistical randomness within the batch.

    Args:
        qubits: Target qubits for the benchmark.
        depths: List of Clifford depths to generate.
        circuits_per_depth: Number of random seeds per depth.
        seed: Master seed for reproducibility.
        native_gates: Basis gate set for decomposition (e.g., ['rz', 'sx', 'cz']).
        clifford_factory: Custom factory for Clifford generation.
        with_measurement: If True, appends measurement gates to all qubits.

    Returns:
        A list of generated QuantumCircuit objects.
    """
    rng = random.Random(seed)
    all_circuits = []

    for depth in depths:
        for i in range(circuits_per_depth):
            c_seed = rng.random()

            # [Call]: Logic + Decomposition happens in Level 2
            circ = generate_single_standard_rb_circuit(
                qubits=qubits,
                depth=depth,
                seed=c_seed,
                clifford_factory=clifford_factory,
                native_gates=native_gates
            )
            circ.metadata["sample_idx"] = i

            # [Call]: Measurement strategy is applied in Level 3
            if with_measurement:
                circ.measure_all()

            all_circuits.append(circ)

    return all_circuits


def generate_respectively_standard_rb_circuits(
        qubit_groups: List[Sequence[int]],
        depths: List[int],
        circuits_per_depth: int,
        same_per_qubit: bool = True,
        seed: Optional[int] = None,
        native_gates: Optional[Union[List[str], str]] = None,
        clifford_factory: Optional[CliffordFactory] = None,
        with_measurement: bool = True
) -> Dict[Tuple[int, ...], Dict[int, List[QuantumCircuit]]]:
    """Generates independent Standard RB circuits for multiple qubit groups."""
    rng = random.Random(seed)
    groups = [tuple(g) for g in qubit_groups]
    results = {g: {d: [] for d in depths} for g in groups}
    template_qubits = list(range(len(groups[0]))) if groups else []

    for d in depths:
        for i in range(circuits_per_depth):
            if same_per_qubit:
                iter_seed = rng.random() if seed is None else (seed + d * 1000 + i)
                # Template is created decomposed
                template = generate_single_standard_rb_circuit(
                    qubits=template_qubits,
                    depth=d,
                    seed=iter_seed,
                    clifford_factory=clifford_factory,
                    native_gates=native_gates
                )
                for g in groups:
                    mapped = remap_circuit_layer(template, target_qubits=g)
                    mapped.metadata["sample_idx"] = i
                    if with_measurement:
                        mapped.measure_all()
                    results[g][d].append(mapped)
            else:
                for g in groups:
                    iter_seed = rng.random()
                    circ = generate_single_standard_rb_circuit(
                        qubits=g,
                        depth=d,
                        seed=iter_seed,
                        clifford_factory=clifford_factory,
                        native_gates=native_gates
                    )
                    circ.metadata["sample_idx"] = i
                    if with_measurement:
                        circ.measure_all()
                    results[g][d].append(circ)

    return results


def generate_simultaneously_standard_rb_circuits(
        qubit_groups: List[Sequence[int]],
        depths: List[int],
        circuits_per_depth: int,
        same_per_qubit: bool = True,
        seed: Optional[int] = None,
        native_gates: Optional[Union[List[str], str]] = None,
        clifford_factory: Optional[CliffordFactory] = None,
        with_measurement: bool = True
) -> Dict[int, List[QuantumCircuit]]:
    """Generates Standard RB circuits where all groups run simultaneously."""
    rng = random.Random(seed)
    groups = [tuple(g) for g in qubit_groups]
    circuits_by_depth = {d: [] for d in depths}
    template_qubits = list(range(len(groups[0]))) if groups else []

    for d in depths:
        for i in range(circuits_per_depth):
            sub_circuits = []
            if same_per_qubit:
                iter_seed = rng.random() if seed is None else (seed + d * 1000 + i)
                template = generate_single_standard_rb_circuit(
                    qubits=template_qubits,
                    depth=d,
                    seed=iter_seed,
                    clifford_factory=clifford_factory,
                    native_gates=native_gates
                )
                for g in groups:
                    sub_circuits.append(remap_circuit_layer(template, target_qubits=g))
            else:
                for g in groups:
                    iter_seed = rng.random()
                    circ = generate_single_standard_rb_circuit(
                        qubits=g,
                        depth=d,
                        seed=iter_seed,
                        clifford_factory=clifford_factory,
                        native_gates=native_gates
                    )
                    sub_circuits.append(circ)

            merged = merge_circuits_layer(sub_circuits)
            merged.metadata["sample_idx"] = i
            merged.metadata["groups"] = groups

            if with_measurement:
                merged.measure_all()

            circuits_by_depth[d].append(merged)

    return circuits_by_depth


# -------------------
# B. Interleaved RB Family
# -------------------

def generate_interleaved_rb_circuits(
        qubits: Sequence[int],
        depths: List[int],
        circuits_per_depth: int,
        interleaved_gate: Gate,
        seed: Optional[int] = None,
        native_gates: Optional[Union[List[str], str]] = None,
        clifford_factory: Optional[CliffordFactory] = None,
        with_measurement: bool = True
) -> List[QuantumCircuit]:
    """Generates a batch of Interleaved RB circuits."""
    rng = random.Random(seed)
    all_circuits = []

    for depth in depths:
        for i in range(circuits_per_depth):
            c_seed = rng.random()

            circ = generate_single_interleaved_rb_circuit(
                qubits=qubits,
                depth=depth,
                interleaved_gate=interleaved_gate,
                seed=c_seed,
                clifford_factory=clifford_factory,
                native_gates=native_gates
            )
            circ.metadata["sample_idx"] = i

            if with_measurement:
                circ.measure_all()

            all_circuits.append(circ)

    return all_circuits


def generate_respectively_interleaved_rb_circuits(
        qubit_groups: List[Sequence[int]],
        depths: List[int],
        circuits_per_depth: int,
        interleaved_gate: Gate,
        same_per_qubit: bool = True,
        seed: Optional[int] = None,
        native_gates: Optional[Union[List[str], str]] = None,
        clifford_factory: Optional[CliffordFactory] = None,
        with_measurement: bool = True
) -> Dict[Tuple[int, ...], Dict[int, List[QuantumCircuit]]]:
    """Generates independent Interleaved RB circuits (Respectively)."""
    rng = random.Random(seed)
    groups = [tuple(g) for g in qubit_groups]
    results = {g: {d: [] for d in depths} for g in groups}
    template_qubits = list(range(len(groups[0]))) if groups else []

    for d in depths:
        for i in range(circuits_per_depth):
            if same_per_qubit:
                iter_seed = rng.random() if seed is None else (seed + d * 1000 + i)
                template = generate_single_interleaved_rb_circuit(
                    qubits=template_qubits,
                    depth=d,
                    interleaved_gate=interleaved_gate,
                    seed=iter_seed,
                    clifford_factory=clifford_factory,
                    native_gates=native_gates
                )
                for g in groups:
                    mapped = remap_circuit_layer(template, target_qubits=g)
                    mapped.metadata["sample_idx"] = i
                    if with_measurement:
                        mapped.measure_all()
                    results[g][d].append(mapped)
            else:
                for g in groups:
                    iter_seed = rng.random()
                    circ = generate_single_interleaved_rb_circuit(
                        qubits=template_qubits,
                        depth=d,
                        interleaved_gate=interleaved_gate,
                        seed=iter_seed,
                        clifford_factory=clifford_factory,
                        native_gates=native_gates
                    )
                    mapped = remap_circuit_layer(circ, target_qubits=g)
                    mapped.metadata["sample_idx"] = i
                    if with_measurement:
                        mapped.measure_all()
                    results[g][d].append(mapped)

    return results


def generate_simultaneously_interleaved_rb_circuits(
        qubit_groups: List[Sequence[int]],
        depths: List[int],
        circuits_per_depth: int,
        interleaved_gate: Gate,
        same_per_qubit: bool = True,
        seed: Optional[int] = None,
        native_gates: Optional[Union[List[str], str]] = None,
        clifford_factory: Optional[CliffordFactory] = None,
        with_measurement: bool = True
) -> Dict[int, List[QuantumCircuit]]:
    """Generates Interleaved RB circuits where all groups run simultaneously."""
    rng = random.Random(seed)
    groups = [tuple(g) for g in qubit_groups]
    circuits_by_depth = {d: [] for d in depths}
    template_qubits = list(range(len(groups[0]))) if groups else []

    for d in depths:
        for i in range(circuits_per_depth):
            sub_circuits = []
            if same_per_qubit:
                iter_seed = rng.random() if seed is None else (seed + d * 1000 + i)
                template = generate_single_interleaved_rb_circuit(
                    qubits=template_qubits,
                    depth=d,
                    interleaved_gate=interleaved_gate,
                    seed=iter_seed,
                    clifford_factory=clifford_factory,
                    native_gates=native_gates
                )
                for g in groups:
                    sub_circuits.append(remap_circuit_layer(template, target_qubits=g))
            else:
                for g in groups:
                    iter_seed = rng.random()
                    circ = generate_single_interleaved_rb_circuit(
                        qubits=template_qubits,
                        depth=d,
                        interleaved_gate=interleaved_gate,
                        seed=iter_seed,
                        clifford_factory=clifford_factory,
                        native_gates=native_gates
                    )
                    sub_circuits.append(remap_circuit_layer(circ, target_qubits=g))

            merged = merge_circuits_layer(sub_circuits)
            merged.metadata["sample_idx"] = i
            merged.metadata["groups"] = groups

            if with_measurement:
                merged.measure_all()

            circuits_by_depth[d].append(merged)

    return circuits_by_depth


# =============================================================================
# Experiment Classes (Interfaces)
# =============================================================================

class StandardRBExperiment:
    """
    Standard Randomized Benchmarking Experiment.

    This class encapsulates the configuration, circuit generation, execution,
    and analysis of a Standard RB experiment. It adheres to industry standards
    by providing state management (caching circuits/results) and simplified
    method signatures.
    """

    def __init__(
            self,
            qubits: Union[int, List[int]],
            depths: List[int] = DEFAULT_RB_DEPTHS,
            circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
            native_gates: Optional[Union[List[str], str]] = None,
            seed: Optional[Union[int, float]] = None,
            clifford_factory: Optional[CliffordFactory] = None,
    ):
        self.qubits = [qubits] if isinstance(qubits, int) else list(qubits)
        self.num_qubits = len(self.qubits)
        self.depths = sorted(set(depths))
        self.circuits_per_depth = circuits_per_depth
        self.native_gates = native_gates
        self.seed = seed
        self.clifford_factory = clifford_factory or CliffordGateSet()

        # State management
        self._circuits: Optional[List[QuantumCircuit]] = None
        self._results: Optional[List[Dict[str, Any]]] = None
        self._analysis_result: Optional[Any] = None

        logging.info(f"Standard RB Configured: Qubits={self.qubits}, Depths={self.depths}")

    def generate_single_standard_rb_circuit(self, depth: int, seed: Optional[float] = None, with_measurement: bool = True) -> QuantumCircuit:
        """Generates a SINGLE circuit for this experiment configuration."""
        # [Call]: native_gates passed to Level 2
        circ = generate_single_standard_rb_circuit(
            qubits=self.qubits,
            depth=depth,
            seed=seed,
            clifford_factory=self.clifford_factory,
            native_gates=self.native_gates
        )
        # [Call]: Only measurement happens here
        if with_measurement:
            circ.measure_all()
        return circ

    def generate_standard_rb_circuits(self, with_measurement: bool = True) -> List[QuantumCircuit]:
        """
        Generates the FULL batch of circuits based on init config.
        Updates self._circuits cache.
        """
        logging.info("Generating RB circuit batch...")
        self._circuits = generate_standard_rb_circuits(
            qubits=self.qubits,
            depths=self.depths,
            circuits_per_depth=self.circuits_per_depth,
            seed=self.seed,
            native_gates=self.native_gates,
            clifford_factory=self.clifford_factory,
            with_measurement=with_measurement
        )
        return self._circuits

    def circuits(self) -> List[QuantumCircuit]:
        """Accessor that employs Lazy Loading."""
        if self._circuits is None:
            return self.generate_standard_rb_circuits()
        return self._circuits

    def run(self, engine: QuantumEngine, shots: int = 1024, plot: bool = True) -> Any:
        """
        Executes the experiment, stitches data, and runs analysis.

        Lifecycle:
        1. Generate circuits (if not exists).
        2. Execute via Engine -> get raw counts.
        3. Stitch Results -> merge counts with circuit metadata.
        4. Analyze -> Curve fit and fidelity calculation.
        5. Plot (optional).

        Args:
            engine: The quantum execution engine.
            shots: Number of shots per circuit.
            plot: Whether to generate plots automatically.

        Returns:
            The Analysis Result object (RBAnalysisResult).
        """
        if self._circuits is None:
            self.generate_standard_rb_circuits()

        logging.info(f"Executing {len(self._circuits)} circuits...")

        # 1. Execution
        execution_results = engine.execute_with_ideal(self._circuits, shots=shots)

        # 2. Stitching (Using the independent helper function)
        self._results = stitch_rb_results(self._circuits, execution_results)

        # 3. Analysis
        logging.info("Analyzing RB data...")
        self._analysis_result = analyze_rb_standard(self._results)

        # 4. Plotting
        if plot:
            try:
                from egm.reporting.visualizers.rb_plotter import plot_rb_results
                plot_rb_results(self._analysis_result)
            except ImportError:
                logging.warning("Plotting skipped: 'egm.reporting.visualizers.rb_plotter' not found.")
            except Exception as e:
                logging.warning(f"Plotting failed: {e}")

        return self._analysis_result


class InterleavedRBExperiment(StandardRBExperiment):
    """
    Configuration holder for Interleaved RB (IRB).
    Generates both Reference (Standard) and Interleaved batches.
    """

    def __init__(
            self,
            interleaved_gate: Gate,
            qubits: Union[int, List[int]],
            depths: List[int] = DEFAULT_RB_DEPTHS,
            circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
            native_gates: Optional[Union[List[str], str]] = None,
            seed: Optional[Union[int, float]] = None,
            clifford_factory: Optional[CliffordFactory] = None,
    ):
        super().__init__(
            qubits=qubits,
            depths=depths,
            circuits_per_depth=circuits_per_depth,
            native_gates=native_gates,
            seed=seed,
            clifford_factory=clifford_factory,
        )
        self.interleaved_gate = interleaved_gate

        # Internal reference experiment instance
        self.reference_experiment = StandardRBExperiment(
            qubits=qubits,
            depths=depths,
            circuits_per_depth=circuits_per_depth,
            native_gates=native_gates,
            seed=seed,
            clifford_factory=clifford_factory,
        )
        self._int_circuits: Optional[List[QuantumCircuit]] = None
        self._results_ref: Optional[List[Dict[str, Any]]] = None
        self._results_int: Optional[List[Dict[str, Any]]] = None

    def generate_single_interleaved_rb_circuit(self, depth: int, seed: Optional[float] = None, with_measurement: bool = True) -> QuantumCircuit:
        """Generates a SINGLE Interleaved circuit (with inline physics)."""
        # [Call]: native_gates passed to Level 2
        circ = generate_single_interleaved_rb_circuit(
            qubits=self.qubits,
            depth=depth,
            interleaved_gate=self.interleaved_gate,
            seed=seed,
            clifford_factory=self.clifford_factory,
            native_gates=self.native_gates
        )
        # [Call]: Only measurement happens here
        if with_measurement:
            circ.measure_all()
        return circ

    def circuits(self, with_measurement: bool = True) -> Dict[str, List[QuantumCircuit]]:
        """Generates both Reference and Interleaved circuits."""
        ref_circuits = self.reference_experiment.circuits()
        for c in ref_circuits: c.metadata["type"] = "reference"

        if self._int_circuits is None:
            self._int_circuits = generate_interleaved_rb_circuits(
                qubits=self.qubits,
                depths=self.depths,
                circuits_per_depth=self.circuits_per_depth,
                interleaved_gate=self.interleaved_gate,
                seed=self.seed,
                native_gates=self.native_gates,
                clifford_factory=self.clifford_factory,
                with_measurement=with_measurement
            )
        for c in self._int_circuits: c.metadata["type"] = "interleaved"

        return {
            "reference": ref_circuits,
            "interleaved": self._int_circuits
        }

    def run(self, engine: QuantumEngine, shots: int = 1024, plot: bool = True) -> Dict[str, Any]:
        """
        Executes and Analyzes the Interleaved RB Experiment.
        """
        circs_dict = self.circuits()
        ref_circs = circs_dict['reference']
        int_circs = circs_dict['interleaved']

        logging.info("Executing Reference Batch...")
        raw_ref = engine.execute_with_ideal(ref_circs, shots=shots)
        # Use helper
        self._results_ref = stitch_rb_results(ref_circs, raw_ref)

        logging.info("Executing Interleaved Batch...")
        raw_int = engine.execute_with_ideal(int_circs, shots=shots)
        # Use helper
        self._results_int = stitch_rb_results(int_circs, raw_int)

        logging.info("Analyzing Interleaved RB data...")
        fit_ref = analyze_rb_standard(self._results_ref)
        fit_int = analyze_rb_standard(self._results_int)

        success = fit_ref.success and fit_int.success
        epg = None

        if success:
            p_ref = next((p.value for p in fit_ref.fit.params if p.name == 'p'), None)
            p_int = next((p.value for p in fit_int.fit.params if p.name == 'p'), None)
            if p_ref is not None and p_int is not None:
                epg = calculate_epg(p_ref, p_int, self.num_qubits)

        self._analysis_result = {
            "success": success,
            "epg": epg,
            "fit_reference": fit_ref,
            "fit_interleaved": fit_int,
            "gate_name": self.interleaved_gate.name
        }

        if plot:
            try:
                from egm.reporting.visualizers.rb_plotter import plot_irb_results
                plot_irb_results(self._analysis_result)
            except ImportError:
                logging.warning("Plotting skipped: 'egm.reporting.visualizers.rb_plotter' not found.")
            except Exception as e:
                logging.warning(f"Plotting failed: {e}")

        return self._analysis_result