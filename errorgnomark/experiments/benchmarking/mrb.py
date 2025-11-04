# File Path: errorgnomark/experiments/benchmarking/mrb.py

import numpy as np
import pandas as pd
import random
from typing import List, Tuple, Dict, Iterable, Optional, Any
from itertools import chain

# --- Internal Framework Imports (Using Absolute Paths) ---
# The previous try-except block has been replaced with direct absolute imports.
# This assumes the 'errorgnomark' package is installed or in the PYTHONPATH.
from errorgnomark.experiments.base import BaseExperiment
from errorgnomark.analysis.result import AnalysisResult
from errorgnomark.circuits.circuit import QuantumCircuit, Gate
from errorgnomark.engine.executor import QuantumEngine
from errorgnomark.analysis.mrb import fit_mrb_decay, MRBFitResult
from errorgnomark.circuits.gate_sets import CliffordGateSet




class MirrorRBExperiment(BaseExperiment):
    """
    Implements the Mirror Randomized Benchmarking (MRB) protocol.

    [V5 ChangeLog]
    - Best Practices: Centralized random number generation for full reproducibility.
    - Efficiency: CliffordGateSet is now instantiated only once.
    - Readability: Added comments to clarify complex logic.
    - This version builds upon the correct logic and bug fixes from V4.

    [V4 ChangeLog]
    - BUG FIX: Corrected the initialization of QuantumCircuit. The constructor
      now receives an explicit list of qubit indices (e.g., `list(qubits)`)
      instead of an integer, resolving the `TypeError: 'int' object is not iterable`.
    """

    def __init__(
        self,
        qubits: List[Tuple[int, ...]],
        depths: List[int],
        circuits_per_depth: int = 20,
        interleaved_gate: Optional[Gate] = None,
        seed: Optional[int] = None,
    ):
        """
        Initializes the Mirror RB experiment.

        Args:
            qubits (List[Tuple[int, ...]]): A list of qubit groups to benchmark.
                Each group must contain an even number of qubits.
            depths (List[int]): A list of circuit depths (number of random Clifford layers).
            circuits_per_depth (int): Number of random circuits per depth.
            interleaved_gate (Optional[Gate]): A gate to interleave for Interleaved MRB.
            seed (Optional[int]): A seed for the random number generator to ensure reproducibility.
        """
        all_qubits_flat = sorted(list(set(chain.from_iterable(qubits))))
        super().__init__(qubits=all_qubits_flat)

        self.qubit_groups = qubits
        self.depths = depths
        self.circuits_per_depth = circuits_per_depth
        self.experiment_type = "MRB"
        self.device_name = "unknown" # Initialize the attribute

        for group in self.qubit_groups:
            if len(group) % 2 != 0:
                raise ValueError(
                    f"MirrorRBExperiment requires an even number of qubits per group. "
                    f"Found group {group} with size {len(group)}."
                )

        self.interleaved_gate = interleaved_gate
        if self.interleaved_gate:
            print(f"Running Interleaved MRB with gate: {self.interleaved_gate.name}")

        # Optimization: Centralize RNG and GateSet instantiation
        self._rng = random.Random(seed)
        self._gate_set = CliffordGateSet()

    def circuits(self) -> Iterable[QuantumCircuit]:
        """
        Generates all quantum circuits for the MRB experiment.
        """
        for i, qubit_group in enumerate(self.qubit_groups):
            for depth in self.depths:
                for j in range(self.circuits_per_depth):
                    # Generate a unique seed for each circuit instance for reproducibility
                    instance_seed = self._rng.random()
                    circuit = self._generate_single_mrb_circuit(
                        qubits=qubit_group,
                        depth=depth,
                        interleaved_gate=self.interleaved_gate,
                        seed=instance_seed
                    )

                    circuit.metadata = {
                        "experiment_type": self.experiment_type,
                        "qubits": qubit_group,
                        "group_id": i,
                        "depth": depth,
                        "x_value": depth,
                        "instance_id": j,
                        "interleaved": self.interleaved_gate is not None
                    }
                    yield circuit

    def run(self, engine: QuantumEngine, **kwargs) -> List[AnalysisResult]:
        """
        Executes the full end-to-end experiment using the Engine v5 architecture.
        """
        print(f"Starting {self.experiment_type} experiment...")
        experiment_circuits = list(self.circuits())
        if not experiment_circuits:
            print("WARNING: No circuits were generated for this experiment.")
            return []
        
        self.device_name = engine.backend.name
        
        shots = kwargs.get('shots')
        if shots is None:
            raise ValueError("The 'shots' argument is required for engine execution.")

        print(f"Generated {len(experiment_circuits)} circuits. Executing on backend '{self.device_name}' with {shots} shots...")

        raw_results = engine.execute_with_ideal(experiment_circuits, shots=shots)

        results_for_df = []
        for circuit, (ideal_probs, noisy_counts) in zip(experiment_circuits, raw_results):
            row_data = circuit.metadata.copy()
            row_data['ideal_probabilities'] = ideal_probs
            row_data['counts'] = noisy_counts
            row_data['shots'] = shots
            results_for_df.append(row_data)
        
        raw_results_df = pd.DataFrame(results_for_df)

        print("Execution complete. Analyzing results...")
        analysis_results = self.analyze(raw_results_df)
        print("Analysis complete.")
        return analysis_results

    def _generate_single_mrb_circuit(
        self,
        qubits: Tuple[int, ...],
        depth: int,
        interleaved_gate: Optional[Gate],
        seed: float
    ) -> QuantumCircuit:
        """
        Generates a single instance of a Mirror RB circuit using CliffordGateSet.
        """
        # Use a local RNG seeded for this specific instance for deterministic generation
        rng = random.Random(seed)

        num_qubits = len(qubits)
        half_n = num_qubits // 2
        qubits_a = qubits[:half_n]
        qubits_b = qubits[half_n:]

        # This is the V4 fix: correctly initialize QuantumCircuit with all qubits.
        circuit = QuantumCircuit(qubits=list(qubits))
        circuit.name = f"mrb_d{depth}_q{qubits}"
        
        forward_clifford_inverses: List[List[Gate]] = []

        # 1. Build the forward random Clifford sequence on the first half of qubits (qubits_a)
        for _ in range(depth):
            forward_gates, inverse_gates = self._gate_set.get_random_clifford_and_inverse(
                qubits=list(qubits_a), seed=rng.random()
            )
            circuit.add_gates(forward_gates)
            forward_clifford_inverses.append(inverse_gates)

        # 2. Add the entangling layer connecting qubits_a to qubits_b
        for i in range(half_n):
            circuit.add_gate(Gate('CNOT', qubits=(qubits_a[i], qubits_b[i])))

        # 3. (Optional) Add the interleaved gate on qubits_a
        if interleaved_gate:
            if not set(interleaved_gate.qubits).issubset(set(qubits_a)):
                raise ValueError(
                    f"Interleaved gate {interleaved_gate} acts on qubits "
                    f"{interleaved_gate.qubits}, which is not a subset of the "
                    f"first half of the group: {qubits_a}."
                )
            circuit.add_gate(interleaved_gate)
            circuit.add_gate(Gate("BARRIER", qubits=qubits))

        # 4. Build the "mirror" part: apply inverse Cliffords in reverse order to qubits_b
        for inverse_gate_list in reversed(forward_clifford_inverses):
            for inv_gate in inverse_gate_list:
                # This is the core "mirror" logic: remap the inverse gate from
                # a qubit in `qubits_a` to its corresponding qubit in `qubits_b`.
                remapped_inv_gate = Gate(
                    name=inv_gate.name,
                    qubits=tuple(qubits_b[qubits_a.index(q)] for q in inv_gate.qubits),
                    params=inv_gate.params
                )
                circuit.add_gate(remapped_inv_gate)
        
        # 5. Add final measurement to all qubits
        circuit.add_gate(Gate("MEASURE", qubits=qubits, is_measurement=True))

        return circuit

    def analyze(self, results: pd.DataFrame) -> List[AnalysisResult]:
        """
        Analyzes the results of the MRB experiment.
        """
        analysis_results = []
        for group_id, group_data in results.groupby('group_id'):
            qubit_group = group_data['qubits'].iloc[0]
            num_qubits_in_group = len(qubit_group)
            
            device_name = self.device_name
            
            print(f"Analyzing MRB results for qubit group: {qubit_group}")

            all_zeros_state = '0' * num_qubits_in_group
            group_data['survival_prob'] = group_data.apply(
                lambda row: row['counts'].get(all_zeros_state, 0) / row['shots'],
                axis=1
            )

            survival_data_for_fit: Dict[int, List[float]] = group_data.groupby('depth')['survival_prob'].apply(list).to_dict()
            fit_result: MRBFitResult = fit_mrb_decay(
                survival_data=survival_data_for_fit,
                num_qubits=num_qubits_in_group
            )

            quality_indicator_value = fit_result['epc']

            detailed_data = {
                "metrics": {
                    "EPC": fit_result['epc'],
                    "EPC_err": fit_result['epc_err'],
                    "p": fit_result['params'][1],
                    "p_err": fit_result['param_errors'][1]
                },
                "fit_parameters": {
                    "A": fit_result['params'][0],
                    "p": fit_result['params'][1],
                    "B": fit_result['params'][2]
                },
                "fit_success": fit_result['fit_successful'],
                "error_message": "Curve fitting failed." if not fit_result['fit_successful'] else None,
                "plot_data": fit_result,
                "raw_survival_data": survival_data_for_fit
            }

            result = AnalysisResult(
                result_type=self.experiment_type,
                device_name=device_name,
                qubits=list(qubit_group),
                quality_indicator=quality_indicator_value,
                data=detailed_data
            )
            
            analysis_results.append(result)

        return analysis_results