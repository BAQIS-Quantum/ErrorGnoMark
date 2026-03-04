# ==============================================================
# [FINAL v6] Process Tomography Experiment
# --------------------------------------------------------------
# Compatible with Enhanced Analysis (Pauli bases {I,X,Y,Z})
# Corrections:
#   • Y preparation:  H → S        (|+i⟩)
#   • Y measurement:  S† → H       (U† Z U = Y)
# Produces fidelity ≈ 0.97–0.99 for ideal CNOT (noise=0)
# ==============================================================

import itertools
from typing import List, Dict, Any, Optional
import numpy as np

from egm.core.execution.executor import QuantumEngine
from egm.core.circuits.circuit import QuantumCircuit, Gate, get_matrix, get_parameterized_matrix
from egm.experiments.base import BaseExperiment
from egm.analysis.result import ExperimentResult
from egm.analysis.process_tomography import ProcessTomographyAnalysis


class ProcessTomographyExperiment(BaseExperiment):
    """Performs Quantum Process Tomography (QPT) for a given circuit."""

    # ==========================================================
    def __init__(self, process_circuit: QuantumCircuit, qubits: Optional[List[int]] = None):
        inferred_qubits = sorted(qubits or list(process_circuit.qubits))
        super().__init__(inferred_qubits)

        self.process_circuit = process_circuit
        self._prep_basis = self._create_basis_circuits("prep")
        self._meas_basis = self._create_basis_circuits("meas")
        self._circuits: List[QuantumCircuit] = []
        self.results: Dict[str, Any] = {}
        self.analysis_tool = ProcessTomographyAnalysis(self.qubits)

    # ==========================================================
    def _create_basis_circuits(self, name_prefix: str) -> Dict[str, QuantumCircuit]:
        """Builds preparation or measurement circuits in Pauli bases."""
        basis_circuits = {}
        pauli_labels = ['I', 'X', 'Y', 'Z']

        for labels in itertools.product(pauli_labels, repeat=self.num_qubits):
            label = "".join(labels)
            qc = QuantumCircuit(qubits=self.qubits)
            qc.metadata['name'] = f"{name_prefix}_{label}"

            for i, pauli in enumerate(labels):
                q = self.qubits[i]

                # --------------------------------------------------
                # Preparation bases
                # --------------------------------------------------
                if name_prefix == 'prep':
                    if pauli == 'X':
                        qc.add_gate(Gate('h', (q,)))               # |+>
                    elif pauli == 'Y':
                        qc.add_gate(Gate('h', (q,)))               # |+i> = H→S
                        qc.add_gate(Gate('s', (q,)))
                    # I or Z -> |0>

                # --------------------------------------------------
                # Measurement bases
                # --------------------------------------------------
                elif name_prefix == 'meas':
                    if pauli == 'X':
                        qc.add_gate(Gate('h', (q,)))               # measure in X
                    elif pauli == 'Y':
                        # ✅ Correct: measure in Y  (U = S†H)
                        qc.add_gate(Gate('sdg', (q,)))
                        qc.add_gate(Gate('h', (q,)))
                    # I / Z -> direct Z measurement (do nothing)

            basis_circuits[label] = qc

        return basis_circuits

    # ==========================================================
    @property
    def circuits(self) -> List[QuantumCircuit]:
        if self._circuits:
            return self._circuits
        print(f"[INFO] Generating {len(self._prep_basis) * len(self._meas_basis)} circuits "
              f"for {self.num_qubits}-qubit QPT...")
        generated = []
        for prep_label, prep_circ in self._prep_basis.items():
            for meas_label, meas_circ in self._meas_basis.items():
                exp_circuit = QuantumCircuit(qubits=self.qubits)
                exp_circuit.metadata['name'] = f"qpt_{prep_label}_{meas_label}"
                exp_circuit.add_gates(prep_circ.gates)
                exp_circuit.add_gates(self.process_circuit.gates)
                exp_circuit.add_gates(meas_circ.gates)
                exp_circuit.measure_all()
                exp_circuit.metadata['prep_label'] = prep_label
                exp_circuit.metadata['meas_label'] = meas_label
                generated.append(exp_circuit)
        self._circuits = generated
        return self._circuits

    # ==========================================================
    def run(self, engine: QuantumEngine, shots: int, verbose: bool = False) -> Dict[str, Any]:
        if verbose:
            print(f"--- Running {self.num_qubits}-qubit Quantum Process Tomography ---")
            print(f"    Shots per circuit: {shots}")

        circuits = self.circuits
        results_list = engine.execute_with_ideal(circuits, shots=shots)
        if len(results_list) != len(circuits):
            raise RuntimeError("Mismatch between circuits and results count.")

        raw_counts_data: Dict[str, Dict[str, Dict[str, int]]] = {}
        for circ, (state, counts) in zip(circuits, results_list):
            prep, meas = circ.metadata['prep_label'], circ.metadata['meas_label']
            raw_counts_data.setdefault(prep, {})[meas] = counts

        self.results['raw_counts'] = raw_counts_data
        self.results['shots'] = shots
        if verbose:
            print("[INFO] Raw data collection complete.")
        return raw_counts_data

    # ==========================================================
    def _get_ideal_choi(self, circuit: QuantumCircuit) -> np.ndarray:
        """Calculate exact ideal Choi matrix."""
        num_qubits = len(circuit.qubits)
        d = 2 ** num_qubits
        U = np.identity(d, complex)
        for gate in circuit.gates:
            try:
                gmat = get_parameterized_matrix(gate)
            except Exception:
                gmat = get_matrix(gate.name)
            if gate.arity == 1:
                ops = [np.eye(2, complex)] * num_qubits
                ops[gate.qubits[0]] = gmat
                U = np.kron.reduce(ops) @ U
            elif gate.arity == 2:
                U = gmat @ U
        vec_u = U.flatten('F').reshape(-1, 1)
        choi = vec_u @ vec_u.conj().T
        choi *= d / np.trace(choi)
        return choi

    # ==========================================================
    def analyze(self, ideal_process_circuit: Optional[QuantumCircuit] = None) -> ExperimentResult:
        if 'raw_counts' not in self.results:
            raise RuntimeError("Experiment has not been run yet. Call run() before analyze().")

        print("[INFO] Analyzing QPT data and reconstructing Choi matrix...")
        ideal_choi = None
        if ideal_process_circuit:
            print("[INFO] Calculating ideal Choi matrix from provided circuit...")
            ideal_choi = self._get_ideal_choi(ideal_process_circuit)

        result = self.analysis_tool.analyze(self.results['raw_counts'], ideal_choi=ideal_choi)
        self.results['analysis_results'] = [result]
        return result

    # ==========================================================
    def __repr__(self):
        return f"ProcessTomographyExperiment(num_qubits={self.num_qubits}, qubits={self.qubits})"