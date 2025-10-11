# File Path: errorgnomark/experiments/benchmarking/mrb.py
# [RESTRUCTURED - To comply with the existing BaseExperiment interface]

from typing import List, Tuple, Dict, Union, Any
import numpy as np

# =========================================================================
# [FIX 1] Correctly import BaseExperiment from the existing 'base.py'
# =========================================================================
from ..base import BaseExperiment
from ...engine import QuantumEngine
from ...circuits.circuit import QuantumCircuit, Gate
from ...analysis.result import ExperimentResult
from ...analysis.mrb import fit_mrb_decay, compute_polarization
from ...analysis.reporting import generate_report, ExcelReport

class MirrorRBExperiment(BaseExperiment):
    """
    Implements Mirror Randomized Benchmarking (MRB).

    This version is adapted to conform to the project's established BaseExperiment interface.
    The `run` method now encapsulates the entire workflow: execution, analysis, and reporting.
    """
    def __init__(
        self,
        qubits: Union[List[int], List[Tuple[int, ...]]],
        depths: List[int],
        circuits_per_depth: int,
        gate_set: str = "clifford",
    ):
        # The base class __init__ might expect a simple list of ints.
        # We handle the complex 'qubits' structure internally.
        # For compatibility, we can pass a flattened list of unique qubit indices to super().
        all_qubit_indices = sorted(list(set(q for group in qubits for q in (group if isinstance(group, tuple) else [group]))))
        super().__init__(qubits=all_qubit_indices)

        self.qubit_groups = qubits # Use a different name to avoid conflict with self.qubits from base class
        self.depths = depths
        self.circuits_per_depth = circuits_per_depth

        from errorgnomark.circuits import gate_sets
        self.gate_set = gate_sets.get_gate_set(gate_set)

        # This will hold the generated circuits after calling circuits()
        self._circuits_map: Dict[str, Dict[int, List[QuantumCircuit]]] = {}

    # =========================================================================
    # [FIX 2] Implement the 'circuits' method as required by the base class
    # =========================================================================
    def circuits(self) -> List[QuantumCircuit]:
        """
        Generates all circuits for all qubit groups and depths for the MRB experiment.
        """
        if self._circuits_map: # If already generated, return flattened list
            return [circ for group_circs in self._circuits_map.values() for depth_circs in group_circs.values() for circ in depth_circs]

        all_circuits = []
        for group in self.qubit_groups:
            group_key = str(group)
            self._circuits_map[group_key] = {}
            for depth in self.depths:
                circs_at_depth = [self._generate_single_circuit(group, depth) for _ in range(self.circuits_per_depth)]
                self._circuits_map[group_key][depth] = circs_at_depth
                all_circuits.extend(circs_at_depth)

        # Store in the format expected by the base class if needed, though we use _circuits_map
        self._circuits = all_circuits
        return self._circuits

    # =========================================================================
    # [FIX 3] Implement the 'run' method with the signature from the base class
    # This method now performs the full end-to-end workflow.
    # =========================================================================
    def run(self, engine: QuantumEngine, shots: int = 1024, verbose: bool = False, report: bool = True, report_path: str = "MRB_Report_Adapted.xlsx") -> List[ExperimentResult]:
        """
        Executes the full MRB experiment: circuit generation, execution, analysis, and reporting.
        """
        # --- Stage 1: Circuit Generation ---
        if not self._circuits_map:
            if verbose: print("[INFO] Generating MRB circuits...")
            self.circuits()

        # --- Stage 2: Data Collection ---
        if verbose: print("[INFO] Running circuits on the backend...")
        survival_data = {str(g): {d: [] for d in self.depths} for g in self.qubit_groups}
        polarization_data = {str(g): {d: [] for d in self.depths} for g in self.qubit_groups}

        for i, group in enumerate(self.qubit_groups):
            group_key = str(group)
            num_qubits = len(group) if isinstance(group, tuple) else 1
            if verbose: print(f"\n--- Processing group: {group} ({i+1}/{len(self.qubit_groups)}) ---")

            for j, depth in enumerate(self.depths):
                if verbose: print(f"  Depth {depth} ({j+1}/{len(self.depths)}): [", end="", flush=True)

                circuits_to_run = self._circuits_map[group_key][depth]
                
                # =========================================================================
                # [BUG FIX] Corrected the method name for batch execution.
                # The QuantumEngine class uses 'execute' for running a batch of circuits, not 'run_batch'.
                # =========================================================================
                batch_results = engine.execute(circuits_to_run, shots=shots)

                for _, noisy_counts in batch_results:
                    survival_prob = self._calculate_survival_probability(noisy_counts, num_qubits)
                    survival_data[group_key][depth].append(survival_prob)

                    polarization = compute_polarization(noisy_counts, num_qubits)
                    polarization_data[group_key][depth].append(polarization)

                    if verbose: print(".", end="", flush=True)
                if verbose: print("] Done.")

        # --- Stage 3: Analysis ---
        if verbose: print("\n[INFO] Analyzing collected data...")
        analysis_results = []
        # Decay fit analysis
        for group in self.qubit_groups:
            num_qubits = len(group) if isinstance(group, tuple) else 1
            group_key = str(group)
            fit_res = fit_mrb_decay(survival_data[group_key], num_qubits)
            result_data = {
                "group": group, "num_qubits": num_qubits,
                "epc": fit_res.get('epc'), "epc_err": fit_res.get('epc_err'),
                "fit_params": fit_res, "raw_data": survival_data[group_key]
            }
            analysis_results.append(ExperimentResult(name=f"MRB Decay Fit ({group})", data=result_data))

        # Direct polarization analysis
        avg_polarizations = [[np.mean(polarization_data[str(g)][d]) for d in self.depths] for g in self.qubit_groups]
        result_data = {
            "qubit_groups": self.qubit_groups, "depths": self.depths,
            "avg_polarizations": avg_polarizations
        }
        analysis_results.append(ExperimentResult(name="MRB Direct Polarization", data=result_data))

        # --- Stage 4: Reporting ---
        if report:
            if verbose: print("[INFO] Generating reports...")
            generate_report(analysis_results)

            if ExcelReport:
                excel_report = ExcelReport(output_dir="reports")
                excel_report.create_summary_sheet(
                    analysis_results,
                    experiment_params={
                        "Experiment": "Mirror RB (Adapted)", "Qubit Groups": str(self.qubit_groups),
                        "Depths": str(self.depths), "Circuits/Depth": self.circuits_per_depth, "Shots": shots
                    }
                )
                for res in analysis_results:
                    if "epc" in res.data: excel_report.add_mrb_decay_plot(res)
                    elif "avg_polarizations" in res.data: excel_report.add_mrb_heatmap(res)
                excel_report.save(report_path)

        return analysis_results

    # --- Helper Methods (Unchanged) ---
    def _calculate_survival_probability(self, counts: Dict[str, int], num_qubits: int) -> float:
        total_shots = sum(counts.values())
        if total_shots == 0: return 0.0
        return counts.get('0' * num_qubits, 0) / total_shots

    def _generate_single_circuit(self, group: Union[int, Tuple[int, ...]], depth: int) -> QuantumCircuit:
        qubits = list(group) if isinstance(group, tuple) else [group]
        num_qubits = len(qubits)
        random_sequence, inverse_sequence = [], []

        for _ in range(depth):
            fwd_layer, inv_layer = [], []
            if num_qubits <= 2:
                fwd_layer, inv_layer = self.gate_set.get_random_clifford_and_inverse(qubits)
            else:
                fwd_1q_sublayer = self.gate_set.get_random_1q_layer(qubits)
                fwd_cnot_sublayer = [Gate(self.gate_set.two_qubit_gate_name, (qubits[i], qubits[i+1])) for i in range(num_qubits - 1)]
                fwd_layer = fwd_1q_sublayer + fwd_cnot_sublayer
                inv_cnot_sublayer = list(reversed(fwd_cnot_sublayer))
                inv_1q_sublayer = [Gate(self.gate_set._inverse_map.get(g.name), g.qubits) for g in reversed(fwd_1q_sublayer)]
                inv_layer = inv_cnot_sublayer + inv_1q_sublayer

            random_sequence.extend(fwd_layer)
            inverse_sequence = inv_layer + inverse_sequence

        return QuantumCircuit(qubits=qubits, gates=random_sequence + inverse_sequence)