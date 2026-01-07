# =============================================================================
# File: examples/new-demos/rb_benchmarking_demo.py
# Version: v5.1 – Standard RB Demo (EGM Schema-Compatible)
# Author : OpenAI‑Assistant
# =============================================================================
"""
Standard Randomized Benchmarking (RB) Demo

Demonstrates the ErrorGnoMark framework with standardized
schemas and reporting integration.

• Runs Standard Randomized Benchmarking (RB) experiments.
• Supports Engine-simulated and User-Data modes.
• Generates Terminal + HTML Reports dynamically.
"""

from __future__ import annotations
import numpy as np
import logging
from uuid import uuid4
from pathlib import Path
import matplotlib.pyplot as plt
import argparse

# -------------------------------------------------------------------
# Framework Imports
# -------------------------------------------------------------------
try:
    # Core backend + engine
    from egm.core.engine.executor import QuantumEngine
    from egm.core.backends.dummy_backend import DummyBackend

    # Experiment
    from egm.core.experiments.benchmarking.rb import StandardRBExperiment

    # Visualization
    from egm.reporting.visualizers.rb_plotter import plot_rb_data

    # Reporting and schema
    from egm.schemas.results.rb import RBAnalysisResult
    from egm.reporting.generators.html_generator import HTMLReportGenerator
    from egm.reporting.generators.terminal_generator import generate_terminal_report

except ImportError as e:
    print(f"[ImportError] {e}")
    print("Ensure ErrorGnoMark is installed correctly (pip install -e .)")
    exit(1)

# -------------------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------
def init_engine(fidelity: float = 0.985, spam_err: float = 5e-4) -> QuantumEngine:
    """Initialize DummyBackend and QuantumEngine for simulation."""
    backend = DummyBackend(clifford_fidelity=fidelity, spam_error_rate=spam_err)
    engine = QuantumEngine(backend=backend)
    return engine


def generate_reports(result_obj, metadata: dict, template_subdir="html") -> None:
    """Generate terminal + HTML reports for a single RB run."""
    print("\n--- Terminal Report ---")
    generate_terminal_report(
        analysis_results=[result_obj],
        experiment_params=metadata,
    )

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    template_dir = Path(f"src/egm/reporting/templates/{template_subdir}")
    html_gen = HTMLReportGenerator(template_dir=template_dir)

    html_path = reports_dir / f"rb_{result_obj.result_id}.html"
    html_gen.generate_rb_report(result=result_obj, output_path=html_path)
    print(f"[Report] HTML saved to: {html_path.resolve()}")


# -------------------------------------------------------------------
# RB Demo Entry
# -------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Standard Randomized Benchmarking Demo (EGM v5)")
    args = parser.parse_args()

    SEED = 2026
    SHOTS = 4096
    DEPTHS = [0, 4, 8, 16, 32, 48, 64]
    CIRCUITS_PER_DEPTH = 20

    print("\n" + "=" * 70)
    print(f" Standard RB Benchmarking Demo (seed={SEED})")
    print("=" * 70)

    engine = init_engine()

    # ================================================================
    # Step 1: Set up Standard RB experiment
    # ================================================================
    exp = StandardRBExperiment(
        qubits=[0, 1],
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        seed=SEED,
    )

    # ================================================================
    # Step 2: Engine-simulated RB Execution
    # ================================================================
    print(f"\n[1/2] Running Engine Mode ... (Standard RB)")
    result_engine = exp.run(engine=engine, shots=SHOTS, plot=True)
    print("[Result] Engine simulation complete.")

    # ================================================================
    # Step 3: User-Data Mode (Re-analysis)
    # ================================================================
    print("\n[2/2] Simulating User-Data Mode ...")

    circuits = exp.circuits()
    user_data = engine.execute_with_ideal(circuits, shots=SHOTS)
    result_user = exp.run(
        engine=engine,
        shots=SHOTS,
        plot=True,
        experimental_results=user_data,
    )
    print("[Result] User data analysis complete.")

    # ================================================================
    # Step 4: Convert to Standardized Schema Object
    # ================================================================
    rb_schema = RBAnalysisResult.from_fit_dict(result_user["rb_fit"], qubits=exp.qubits)
    rb_schema.success = rb_schema.fit.success or result_user.get("fit_successful", False)
    rb_schema.notes = f"Standard RB demo ({SHOTS} shots per circuit)."

    # Diagnostic print
    print(f"\n[Schema] EPC = {rb_schema.epc:.3e} ± {rb_schema.epc_error if rb_schema.epc_error else 0:.2e}")

    # ================================================================
    # Step 5: Generate Reports
    # ================================================================
    metadata = {
        "Workflow": "Standard RB Demo (v5)",
        "Experiment Type": "RB",
        "Qubits": exp.qubits,
        "Depths": exp.depths,
        "Shots per Circuit": SHOTS,
    }
    generate_reports(rb_schema, metadata)

    print("\n" + "=" * 70)
    print(" Standard RB Demo Completed Successfully ")
    print("=" * 70)

    # Keep figures visible
    plt.show()


# -------------------------------------------------------------------
# Main Entrypoint
# -------------------------------------------------------------------
if __name__ == "__main__":
    main()