# File: examples/new-demos/new_rb_demo_q1q2.py
# ---------------------------------------------------------------
# Example: End-to-End Randomized Benchmarking (RB) Workflow Demo
# ---------------------------------------------------------------
# This demonstration shows two workflows for performing a complete
# Randomized Benchmarking experiment using the ErrorGnoMark framework:
#   1. Fully automated analysis and report generation.
#   2. Step-by-step manual procedure.
#
# This version follows Pydantic 2.x validation models and uses
# the new HTML and terminal report generators along with the
# matplotlib-based visualizer.
# ---------------------------------------------------------------

import numpy as np
import logging
from uuid import uuid4
from pathlib import Path
import matplotlib.pyplot as plt

# --- Framework Imports ---
try:
    from egm.core.experiments.benchmarking.rb import StandardRBExperiment
    from egm.core.engine.executor import QuantumEngine
    from egm.core.backends.dummy_backend import DummyBackend
    from egm.core.analysis.rb import fit_rb_data
    from egm.schemas.results.rb import RBAnalysisResult, RBSequenceDataPoint
    from egm.schemas.results.base import FitResult, FitParameter
    from egm.reporting.generators.html_generator import HTMLReportGenerator
    from egm.reporting.generators.terminal_generator import generate_terminal_report
    from egm.reporting.visualizers.rb_plotter import plot_rb_data
except ImportError as e:
    print(f"ImportError: {e}")
    print(
        "The 'errorgnomark' package could not be imported. "
        "Please install the project first by running 'pip install -e .' "
        "from the repository root directory."
    )
    exit(1)

# Configure global logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def main() -> None:
    """Run both the automated and manual RB workflows."""
    DEMO_SEED = 42
    print(f"\n--- EGM RB Demo Workflow (Seed = {DEMO_SEED}) ---")

    # --- Experimental parameters ---
    CLIFFORD_FIDELITY = 0.985
    SPAM_ERROR = 0.0005
    NUM_SHOTS = 8192

    print(f"Initializing DummyBackend (Clifford Fidelity = {CLIFFORD_FIDELITY}) ...")
    backend = DummyBackend(
        clifford_fidelity=CLIFFORD_FIDELITY,
        spam_error_rate=SPAM_ERROR,
    )
    engine = QuantumEngine(backend=backend)

    # Standard RB experiment configuration
    rb_params = {
        "qubits": [0, 1],
        "depths": [2, 8, 16, 24, 32, 48, 64],
        "circuits_per_depth": 30,
    }

    # ================================================================
    # Part 1: Automated End-to-End Workflow
    # ================================================================
    print("\n" + "=" * 70)
    print(" Part 1: Fully Automated RB Workflow ")
    print("=" * 70)

    rb_exp_auto = StandardRBExperiment(**rb_params, seed=DEMO_SEED)

    print(
        f"\nRunning full RB experiment for qubits {rb_exp_auto.qubits} "
        "using `experiment.run(plot=True)` ..."
    )

    auto_results_dict = rb_exp_auto.run(
        engine=engine,
        shots=NUM_SHOTS,
        plot=True,
    )

    if auto_results_dict and auto_results_dict.get("fit_successful"):
        print("\nRB execution and fitting complete. Generating formal reports ...")

        # Construct FitResult using Pydantic model
        fit_obj = FitResult(
            model_name="rb_exponential_decay",
            params=[
                FitParameter(
                    name="A",
                    value=auto_results_dict["params"]["A"],
                    std_dev=auto_results_dict["param_errors"]["A"],
                ),
                FitParameter(
                    name="p",
                    value=auto_results_dict["params"]["p"],
                    std_dev=auto_results_dict["param_errors"]["p"],
                ),
                FitParameter(
                    name="B",
                    value=auto_results_dict["params"]["B"],
                    std_dev=auto_results_dict["param_errors"]["B"],
                ),
            ],
        )

        # Construct RBAnalysisResult
        auto_result_obj = RBAnalysisResult(
            analyzer_version="2.2",
            qubits=rb_exp_auto.qubits,
            plan_id=uuid4(),
            raw_data_ids=[uuid4() for _ in rb_exp_auto.depths],
            tags=["automated_run", "demo_workflow"],
            notes=f"Automated demo run ({NUM_SHOTS} shots per circuit).",
            success=auto_results_dict["fit_successful"],
            fit=fit_obj,
            error_message=auto_results_dict.get("error_message"),
            depths=auto_results_dict["x_data"],
            means=auto_results_dict["y_data"],
            stds=auto_results_dict["y_err"],
            sequence_data=[
                RBSequenceDataPoint(
                    sequence_length=int(x),
                    survival_probability=float(y),
                    std_error=float(err),
                )
                for x, y, err in zip(
                    auto_results_dict["x_data"],
                    auto_results_dict["y_data"],
                    auto_results_dict["y_err"],
                )
            ],
        )

        print("\n--- Terminal Report (Automated Run) ---")
        experiment_metadata = {
            "Workflow": "Automated End-to-End",
            "Experiment Type": "Standard RB",
            "Qubits": rb_exp_auto.qubits,
            "Depths": rb_exp_auto.depths,
            "Circuits per Depth": rb_exp_auto.circuits_per_depth,
            "Shots per Circuit": NUM_SHOTS,
        }
        generate_terminal_report(
            analysis_results=[auto_result_obj],
            experiment_params=experiment_metadata,
        )

        # Generate HTML report
        output_dir = Path("reports")
        output_dir.mkdir(exist_ok=True)
        template_path = Path("src/egm/reporting/templates/html")

        html_generator = HTMLReportGenerator(template_dir=template_path)
        report_path = output_dir / f"rb_report_auto_{auto_result_obj.result_id}.html"
        html_generator.generate_rb_report(result=auto_result_obj, output_path=report_path)

        print(f"\nHTML report saved to: {report_path.resolve()}")
    else:
        logging.error("Automated RB run failed to complete successfully.")

    input("\nPress Enter to continue to Part 2 (Manual Workflow)...")

    # ================================================================
    # Part 2: Manual Step-by-Step Workflow
    # ================================================================
    print("\n" + "=" * 70)
    print(" Part 2: Manual Workflow (Step-by-Step) ")
    print("=" * 70)

    rb_exp_manual = StandardRBExperiment(**rb_params, seed=DEMO_SEED + 1)

    # --- Step 1: Circuit generation ---
    print("\n[Step 1] Generating RB circuits ...")
    circuits = rb_exp_manual.circuits()

    # --- Step 2: Circuit execution ---
    print("\n[Step 2] Executing circuits ...")
    raw_results = engine.execute_with_ideal(circuits, shots=NUM_SHOTS)

    # --- Step 3: Aggregate results ---
    print("\n[Step 3] Aggregating survival probabilities ...")
    agg_results = rb_exp_manual.aggregate(raw_results, shots=NUM_SHOTS)

    # --- Step 4: Data fitting ---
    print("\n[Step 4] Performing RB fitting ...")
    manual_fit_dict = fit_rb_data(
        depths=agg_results["depths"],
        means=agg_results["means"],
        stds=agg_results["stds"],
        num_qubits=rb_exp_manual.num_qubits,
    )
    if not manual_fit_dict.get("fit_successful"):
        logging.error("Manual RB fitting failed.")
        return
    print(f"Fit successful. EPC = {manual_fit_dict['epc']:.4e}")

    # --- Step 5: Plot results ---
    print("\n[Step 5] Generating visualization and reports ...")

    fig, ax = plt.subplots(figsize=(8, 5))
    plot_rb_data(
        results=manual_fit_dict,
        ax=ax,
        title=f"Manual RB Analysis ({rb_exp_manual.num_qubits} qubits)",
    )
    plt.show()

    # Build FitResult and wrap it into RBAnalysisResult
    fit_obj_manual = FitResult(
        model_name="rb_exponential_decay",
        params=[
            FitParameter(
                name="A",
                value=manual_fit_dict["params"]["A"],
                std_dev=manual_fit_dict["param_errors"]["A"],
            ),
            FitParameter(
                name="p",
                value=manual_fit_dict["params"]["p"],
                std_dev=manual_fit_dict["param_errors"]["p"],
            ),
            FitParameter(
                name="B",
                value=manual_fit_dict["params"]["B"],
                std_dev=manual_fit_dict["param_errors"]["B"],
            ),
        ],
    )

    manual_result_obj = RBAnalysisResult(
        analyzer_version="2.2",
        qubits=rb_exp_manual.qubits,
        plan_id=uuid4(),
        raw_data_ids=[uuid4() for _ in rb_exp_manual.depths],
        tags=["manual_run", "demo_workflow"],
        notes=f"Manual RB demo run ({NUM_SHOTS} shots per circuit).",
        success=manual_fit_dict["fit_successful"],
        fit=fit_obj_manual,
        error_message=manual_fit_dict.get("error_message"),
        depths=manual_fit_dict["x_data"],
        means=manual_fit_dict["y_data"],
        stds=manual_fit_dict["y_err"],
        sequence_data=[
            RBSequenceDataPoint(
                sequence_length=int(x),
                survival_probability=float(y),
                std_error=float(err),
            )
            for x, y, err in zip(
                manual_fit_dict["x_data"],
                manual_fit_dict["y_data"],
                manual_fit_dict["y_err"],
            )
        ],
    )

    print("\n--- Terminal Report (Manual Run) ---")
    exp_params_manual = {
        "Workflow": "Manual Step-by-Step",
        "Experiment Type": "Standard RB",
        "Qubits": rb_exp_manual.qubits,
    }
    generate_terminal_report(
        analysis_results=[manual_result_obj],
        experiment_params=exp_params_manual,
    )

    report_path_manual = Path("reports") / f"rb_report_manual_{manual_result_obj.result_id}.html"
    html_generator.generate_rb_report(result=manual_result_obj, output_path=report_path_manual)

    print(f"\nHTML report saved to: {report_path_manual.resolve()}")

    print("\n" + "=" * 70)
    print(" Demo Workflow Completed Successfully ")
    print("=" * 70)


if __name__ == "__main__":
    main()