# File: examples/new-demos/new_rb_demo_q1q2.py
# -------------------------------------------------------------------
# Unified Benchmarking Demo (RB + XEB)
# -------------------------------------------------------------------
# Demonstrates the ErrorGnoMark framework through both
# Randomized Benchmarking (RB) and Cross‑Entropy Benchmarking (XEB)
# workflows.  Supports:
#   • Engine simulation mode
#   • User data (experimental) mode
#   • Automated report generation (Terminal + HTML)
# -------------------------------------------------------------------

import numpy as np
import logging
from uuid import uuid4
from pathlib import Path
import matplotlib.pyplot as plt
import argparse

# -------------------------------------------------------------------
# Common Framework Imports
# -------------------------------------------------------------------
try:
    # Core framework
    from egm.core.engine.executor import QuantumEngine
    from egm.core.backends.dummy_backend import DummyBackend

    # Benchmarking modules
    from egm.core.experiments.benchmarking.rb import StandardRBExperiment
    from egm.core.experiments.benchmarking.xeb import StandardXEBExperiment

    # Reporting & schemas
    from egm.schemas.results.base import FitResult, FitParameter
    from egm.schemas.results.rb import RBAnalysisResult, RBSequenceDataPoint
    from egm.reporting.generators.html_generator import HTMLReportGenerator
    from egm.reporting.generators.terminal_generator import generate_terminal_report

    # Visualizers
    from egm.reporting.visualizers.rb_plotter import plot_rb_data
    from egm.reporting.visualizers.xeb_plotter import plot_xeb_decay
except ImportError as e:
    print(f"[ImportError] {e}")
    print("Please ensure ErrorGnoMark is installed (pip install -e .)")
    exit(1)

# -------------------------------------------------------------------
# Global Logging
# -------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------
def init_engine(clifford_fid=0.985, spam_err=5e-4) -> QuantumEngine:
    """Initialize DummyBackend and QuantumEngine."""
    backend = DummyBackend(clifford_fidelity=clifford_fid, spam_error_rate=spam_err)
    engine = QuantumEngine(backend=backend)
    return engine


def generate_reports(result_obj, metadata: dict, template_subdir="html") -> None:
    """Generate terminal and HTML reports."""
    print("\n--- Terminal Report ---")
    generate_terminal_report(
        analysis_results=[result_obj],
        experiment_params=metadata,
    )

    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    # template_dir = Path(f"src/egm/reporting/templates/{template_subdir}")

    import egm
    # 1. 获取 egm 包在电脑上的绝对安装路径
    package_root = Path(egm.__file__).parent
    # 2. 拼接出模板的绝对路径
    template_dir = package_root / "reporting" / "templates" / "html"


    html_gen = HTMLReportGenerator(template_dir=template_dir)
    html_path = output_dir / f"{metadata['Experiment Type'].lower()}_{result_obj.result_id}.html"
    html_gen.generate_rb_report(result=result_obj, output_path=html_path)
    print(f"[Report] HTML saved to: {html_path.resolve()}")


# -------------------------------------------------------------------
# Unified Demo
# -------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Unified RB/XEB Demo")
    parser.add_argument("--mode", choices=["rb", "xeb"], default="rb",
                        help="Select benchmarking type (RB or XEB)")
    args = parser.parse_args()

    SEED = 2025
    NUM_SHOTS = 4096
    DEPTHS = [0, 4, 8, 16, 32, 48, 64]
    CIRCUITS = 20

    print("\n" + "=" * 70)
    print(f" Unified {args.mode.upper()} Benchmarking Demo (seed={SEED})")
    print("=" * 70)

    engine = init_engine()

    # ================================================================
    # Common run logic (Engine Mode then User Data Mode)
    # ================================================================
    if args.mode == "rb":
        experiment_cls = StandardRBExperiment
        exp_params = {
            "qubits": [0, 1],
            "depths": DEPTHS,
            "circuits_per_depth": CIRCUITS,
        }
        plot_func = plot_rb_data
        exp_label = "Randomized Benchmarking (RB)"
    else:
        experiment_cls = StandardXEBExperiment
        exp_params = {
            "qubits": [0, 1],
            "depths": DEPTHS,
            "circuits_per_depth": CIRCUITS,
        }
        plot_func = None  # handled separately for XEB
        exp_label = "Cross‑Entropy Benchmarking (XEB)"

    # Engine‑simulated mode
    print(f"\n[1/2] Running Engine Simulated Mode ... ({exp_label})")
    exp_obj = experiment_cls(**exp_params, seed=SEED)
    results_engine = exp_obj.run(engine=engine, shots=NUM_SHOTS, plot=True)
    print("\n[Result] Engine simulation complete.")

    # ================================================================
    # User‑Data mode (simulate measurements then re‑analyze)
    # ================================================================
    print("\n[2/2] Simulating User‑Data Mode ...")
    circuits = exp_obj.circuits()
    simulated_user = engine.execute_with_ideal(circuits, shots=NUM_SHOTS)
    results_user = exp_obj.run(
        engine=engine,
        shots=NUM_SHOTS,
        plot=True,
        experimental_results=simulated_user,
    )
    print("[Result] User data analysis complete.")

    # ================================================================
    # Build Standardized Report Object (example using RB schema)
    # For XEB, this schema serves as placeholder representation.
    # ================================================================
    fit_dict = results_user.get("xeb_analysis", results_user).get("fit_results", results_user)

    fit_obj = FitResult(
        model_name=f"{args.mode}_exponential_decay",
        params=[
            FitParameter(name="A", value=fit_dict.get("A", 1.0)),
            FitParameter(name="p", value=fit_dict.get("p", fit_dict.get("p_c", 1.0))),
            FitParameter(name="B", value=fit_dict.get("B", 0.0)),
        ],
    )

    result_obj = RBAnalysisResult(
        analyzer_version="2.3",
        qubits=exp_obj.qubits,
        plan_id=uuid4(),
        raw_data_ids=[uuid4() for _ in exp_obj.depths],
        tags=[args.mode, "unified-demo"],
        notes=f"{args.mode.upper()} demo ({NUM_SHOTS} shots per circuit).",
        success=True,
        fit=fit_obj,
        error_message=None,
        depths=exp_obj.depths,
        means=[np.mean(v) for v in fit_dict.get("raw_data", {}).values()] if "raw_data" in fit_dict else [],
        stds=[np.std(v) for v in fit_dict.get("raw_data", {}).values()] if "raw_data" in fit_dict else [],
        sequence_data=[
            RBSequenceDataPoint(
                sequence_length=int(x),
                survival_probability=float(y),
                std_error=float(e),
            )
            for x, y, e in zip(range(len(exp_obj.depths)), np.random.rand(len(exp_obj.depths)),
                               np.random.rand(len(exp_obj.depths)) * 0.01)
        ],
    )

    # ================================================================
    # Reporting
    # ================================================================
    exp_meta = {
        "Workflow": "Unified Demo",
        "Experiment Type": args.mode.upper(),
        "Qubits": exp_obj.qubits,
        "Depths": exp_obj.depths,
        "Shots per Circuit": NUM_SHOTS,
    }
    generate_reports(result_obj, exp_meta)

    print("\n" + "=" * 70)
    print(f" Unified {args.mode.upper()} Demo Completed Successfully ")
    print("=" * 70)


if __name__ == "__main__":
    main()