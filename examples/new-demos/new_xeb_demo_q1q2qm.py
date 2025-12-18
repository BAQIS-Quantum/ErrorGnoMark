# File Path: examples/demo_xeb_q1q2qm.py
# [EGM v4.3 – Unified/Modernized Cross‑Entropy Benchmarking Demo]
# ---------------------------------------------------------------------
# Demonstrates the complete XEB workflow using the updated v4 architecture.
# Features:
#   • Compatible with DummyBackend (XEB‑specific noise model)
#   • Circuit generation & compilation showcase
#   • Bulk circuit production
#   • Automated dual‑mode (Engine & User‑Data) analysis
#   • Consistent with RB Demo reporting/visualization style
# ---------------------------------------------------------------------

import sys, os, logging
import numpy as np
from pathlib import Path
from uuid import uuid4
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Environment Pathing — ensure top‑level import works in examples/
# ---------------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ---------------------------------------------------------------------
# Framework Imports
# ---------------------------------------------------------------------
try:
    from egm.core.engine.executor import QuantumEngine
    from egm.core.backends.dummy_backend_xeb import DummyBackend
    from egm.core.circuits.circuit import Gate
    from egm.core.experiments.benchmarking.xeb import StandardXEBExperiment, InterleavedXEBExperiment
    from egm.reporting.visualizers.xeb_plotter import plot_xeb_decay, plot_spb_decay
    from egm.schemas.results.base import FitResult, FitParameter
    from egm.schemas.results.rb import RBAnalysisResult, RBSequenceDataPoint
    from egm.reporting.generators.terminal_generator import generate_terminal_report
    from egm.reporting.generators.html_generator import HTMLReportGenerator
except ImportError as e:
    print(f"[ImportError] {e}")
    print("Please install ErrorGnoMark with: pip install -e .")
    sys.exit(1)

# Logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# =====================================================================
# Helper Utilities
# =====================================================================
def init_engine():
    """Initialize DummyBackend and QuantumEngine for XEB."""
    backend = DummyBackend(cycle_fidelity=0.998, spam_error=0.0001)
    engine = QuantumEngine(backend)
    print(f"Initialized DummyBackend '{backend.name}' "
          f"(Cycle Fidelity = {backend.cycle_fidelity:.4f}, EPC ≈ {1 - backend.cycle_fidelity:.5f})")
    return engine


def generate_reports(result_obj, exp_meta: dict, template_subdir="html"):
    """Generate unified terminal + HTML reports."""
    print("\n--- Terminal Report ---")
    generate_terminal_report(analysis_results=[result_obj], experiment_params=exp_meta)
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    html_gen = HTMLReportGenerator(template_dir=Path(f"src/egm/reporting/templates/{template_subdir}"))
    output_path = output_dir / f"{exp_meta['Experiment Type'].lower()}_{result_obj.result_id}.html"
    html_gen.generate_rb_report(result=result_obj, output_path=output_path)
    print(f"[Report] HTML saved to: {output_path.resolve()}")


# =====================================================================
# CUSTOM NATIVE GATE SET (for compilation showcase)
# =====================================================================
CUSTOM_NATIVE_GATES = {"id": 1, "sx": 1, "rz": 1, "cz": 2}


# =====================================================================
# MAIN DEMONSTRATION
# =====================================================================
def main():
    DEMO_SEED = 42
    NUM_SHOTS = 4096
    print("\n" + "=" * 80)
    print(" EGMLab Demonstration — Cross‑Entropy Benchmarking (XEB)")
    print("=" * 80)
    engine = init_engine()

    # ================================================================
    # PART 1 — CIRCUIT GENERATION AND COMPILATION SHOWCASE
    # ================================================================
    print("\n" + "=" * 80)
    print(" PART 1 — CIRCUIT GENERATION & COMPILATION")
    print("=" * 80)

    print("\n[1a] Logical circuit generation:")
    logical_exp = StandardXEBExperiment(qubits=[0, 1], seed=DEMO_SEED)
    logical_circuit = logical_exp.generate_single_circuit(depth=8, seed=1)
    logical_circuit.draw()

    print("\n[1b] Compilation to custom native gate set:")
    compiled_exp = StandardXEBExperiment(
        qubits=[0, 1],
        native_gates=list(CUSTOM_NATIVE_GATES.keys()),
        seed=DEMO_SEED,
    )
    compiled_circuit = compiled_exp.generate_single_circuit(depth=8, seed=1)
    compiled_circuit.draw()

    print("\n[1c] Interleaved circuit example:")
    inter_gate = Gate("u3", (0,), params=[np.pi / 2, np.pi / 4, -np.pi / 4])
    inter_exp = InterleavedXEBExperiment(
        qubits=[0, 1],
        interleaved_gate=inter_gate,
        native_gates=list(CUSTOM_NATIVE_GATES.keys()),
    )
    inter_circuit = inter_exp.generate_single_circuit(depth=12, seed=2)
    inter_circuit.draw()
    print("Circuit examples generated successfully.\n")

    # ================================================================
    # PART 2 — BULK CIRCUIT GENERATION
    # ================================================================
    print("\n" + "=" * 80)
    print(" PART 2 — BULK CIRCUIT GENERATION")
    print("=" * 80)
    depths = [10, 20, 30, 40, 50]
    bulk = StandardXEBExperiment(
        qubits=[0, 1, 2, 3],
        depths=depths,
        circuits_per_depth=10,
        native_gates=list(CUSTOM_NATIVE_GATES.keys()),
    )
    circuits = bulk.circuits()
    print(f"Generated {len(circuits)} circuits for qubits [0,1,2,3] at depths {depths}.\n")

    # ================================================================
    # PART 3 — AUTOMATED EXPERIMENT (ENGINE MODE)
    # ================================================================
    print("\n" + "=" * 80)
    print(" PART 3 — AUTOMATED EXPERIMENT (ENGINE MODE)")
    print("=" * 80)

    auto_exp = StandardXEBExperiment(
        qubits=[0, 1],
        depths=[0, 20, 50, 100, 150, 200, 250],
        circuits_per_depth=25,
        seed=DEMO_SEED,
    )

    print("[Running] Automated XEB execution... (plot will appear)")
    results_auto = auto_exp.run(engine=engine, shots=NUM_SHOTS, plot=True)
    print("\n[Result] Engine‑mode XEB complete.")

    # ================================================================
    # PART 4 — USER EXPERIMENT DATA MODE
    # ================================================================
    print("\n" + "=" * 80)
    print(" PART 4 — USER EXPERIMENT RESULTS MODE")
    print("=" * 80)

    print("[Simulating] Generating pseudo‑experimental data from engine...")
    circuits_user = auto_exp.circuits()
    simulated_user = engine.execute_with_ideal(circuits_user, shots=NUM_SHOTS)

    print("[Running] Direct analysis of user‑provided experimental data… (no backend calls)")
    results_user = auto_exp.run(
        engine=engine,
        shots=NUM_SHOTS,
        plot=True,
        experimental_results=simulated_user,
    )
    print("\ User‑data analysis finished successfully.\n")

    # ================================================================
    # PART 5 — REPORT GENERATION
    # ================================================================
    print("\n" + "=" * 80)
    print(" PART 5 — REPORT GENERATION (DEMO)")
    print("=" * 80)

    fit_data = results_user["xeb_analysis"]["fit_results"]
    fit_obj = FitResult(
        model_name="xeb_exponential_decay",
        params=[
            FitParameter(name="A", value=fit_data["A"]),
            FitParameter(name="p", value=fit_data["p"]),
            FitParameter(name="B", value=fit_data["B"]),
        ],
    )

    # Package results in generic RBAnalysisResult schema (used as stand‑in for XEB)
    report_obj = RBAnalysisResult(
        analyzer_version="4.3",
        qubits=auto_exp.qubits,
        plan_id=uuid4(),
        raw_data_ids=[uuid4() for _ in auto_exp.depths],
        tags=["xeb", "demo", "user‑data‑mode"],
        notes=f"XEB demo ({NUM_SHOTS} shots per circuit).",
        success=True,
        fit=fit_obj,
        depths=auto_exp.depths,
        means=[np.mean(v) for v in results_user["xeb_analysis"]["raw_data"].values()],
        stds=[np.std(v) for v in results_user["xeb_analysis"]["raw_data"].values()],
        sequence_data=[
            RBSequenceDataPoint(
                sequence_length=int(d),
                survival_probability=float(np.mean(vals)),
                std_error=float(np.std(vals) / np.sqrt(len(vals))),
            )
            for d, vals in results_user["xeb_analysis"]["raw_data"].items()
        ],
    )

    exp_meta = {
        "Workflow": "XEB Demo (Engine + User Modes)",
        "Experiment Type": "XEB",
        "Qubits": auto_exp.qubits,
        "Depths": auto_exp.depths,
        "Shots per Circuit": NUM_SHOTS,
    }

    generate_reports(report_obj, exp_meta)

    print("\n" + "=" * 80)
    print(" XEB DEMO COMPLETE — All stages executed successfully. ")
    print("=" * 80)


if __name__ == "__main__":
    main()