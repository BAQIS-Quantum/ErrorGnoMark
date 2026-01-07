# =============================================================================
# File: examples/sisq-egm-consistent-demo/demo_xeb_q1q2qm.py
# Version: v5.1.4 – Final Clean Edition (1Q + 2Q CZ Interleaved + 4Q Standard)
# Author : OpenAI-Assistant
# =============================================================================
"""
EGM‑v5 Consistent XEB Demo — 1‑Qubit, 2‑Qubit CZ Interleaved, and 4‑Qubit
=========================================================================

Demonstrates three Cross‑Entropy Benchmarking (XEB) experiments using
the EGM‑Core environment:

1. Single‑qubit XEB fidelity‑decay + EPC estimation
2. Two‑qubit Interleaved‑XEB (target gate = CZ)
3. Four‑qubit standard XEB decay benchmark

All results follow the unified RB‑style result schema (EGM v5 core)
and automatically generate HTML / terminal reports.

Usage
-----
$ python -m examples.sisq-egm-consistent-demo.demo_xeb_q1q2qm
"""

from __future__ import annotations
import logging
from uuid import uuid4
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Framework Imports
# ---------------------------------------------------------------------------
from egm.core.engine.executor import QuantumEngine
from egm.core.backends.dummy_backend_xeb import DummyBackend
from egm.core.experiments.benchmarking.xeb import (
    StandardXEBExperiment,
    InterleavedXEBExperiment,
)
from egm.core.circuits.circuit import Gate
from egm.schemas.results.xeb import XEBAnalysisResult
from egm.reporting.generators.terminal_generator import generate_terminal_report
from egm.reporting.generators.html_generator import HTMLReportGenerator

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global parameters
# ---------------------------------------------------------------------------
DEPTHS = [0, 1, 2, 4, 6, 8, 12, 16, 24, 40]
CIRCUITS_PER_DEPTH = 50
SHOTS = 8096

# ---------------------------------------------------------------------------
# Engine initialization
# ---------------------------------------------------------------------------
def init_engine() -> QuantumEngine:
    """Return a DummyBackend‑driven QuantumEngine for simulation."""
    backend = DummyBackend(
        cycle_fidelity=0.9985,
        noise_strength=0.9,
        two_qubit_boost=6.0,
        jitter_scale=0.0001,
    )
    return QuantumEngine(backend=backend)

# ---------------------------------------------------------------------------
# Reporting utilities
# ---------------------------------------------------------------------------
def generate_reports(result_obj, metadata: dict, template_subdir: str = "html"):
    """Generate terminal + HTML reports."""
    print("\n--- Terminal Report ---")
    generate_terminal_report([result_obj], experiment_params=metadata)

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    template_dir = Path(f"src/egm/reporting/templates/{template_subdir}")

    html_gen = HTMLReportGenerator(template_dir=template_dir)
    html_path = (
        reports_dir / f"{metadata['Experiment Type'].replace(' ', '_').lower()}_{uuid4().hex[:6]}.html"
    )
    html_gen.generate_rb_report(result=result_obj, output_path=html_path)
    print(f"[Report] HTML saved to: {html_path.resolve()}\n")

# ---------------------------------------------------------------------------
# 1. Single‑Qubit XEB
# ---------------------------------------------------------------------------
def single_qubit_xeb_demo(engine: QuantumEngine) -> None:
    """Run a single‑qubit standard XEB decay and EPC estimation."""
    print("\n" + "=" * 70)
    print(" [1‑Qubit] Standard XEB Decay + EPC Estimation ".center(70, "="))
    print("=" * 70)

    xeb_exp = StandardXEBExperiment(
        qubits=[0],
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        x_axis_mode="depth",
    )

    res = xeb_exp.run(engine=engine, shots=SHOTS, plot=True, debug=False)
    plt.close("all")  # prevent stray blank figures

    epc = res["xeb_analysis"]["fit_results"]["epc"]
    print(f"[RESULT] 1‑Qubit XEB EPC ≈ {epc:.4e}")

    schema = XEBAnalysisResult(
        qubits=[0],
        axis_mode="depth",
        depths=list(res["xeb_analysis"]["raw_data"].keys()),
        mean_fidelity=list(res["xeb_analysis"]["raw_data"].values()),
        fit=res["xeb_analysis"]["fit_results"],
    )

    metadata = {
        "Experiment Type": "Standard‑XEB‑1Q",
        "Qubits": [0],
        "Depths": DEPTHS,
    }
    generate_reports(schema, metadata)

# ---------------------------------------------------------------------------
# 2. Two‑Qubit Interleaved‑XEB (Target = CZ)
# ---------------------------------------------------------------------------
def two_qubit_interleaved_demo(engine: QuantumEngine) -> None:
    """Run a 2‑qubit Interleaved‑XEB benchmark for a CZ gate."""
    print("\n" + "=" * 70)
    print(" [2‑Qubit] Interleaved‑XEB (CZ Gate) ".center(70, "="))
    print("=" * 70)

    cz_gate = Gate("cz", qubits=(0, 1))

    exp_gc = InterleavedXEBExperiment(
        qubits=[0, 1],
        interleaved_gate=cz_gate,
        depths=[0, 4, 6, 8, 12, 16, 24, 32, 40],
        circuits_per_depth=50,
        seed=42,
        x_axis_mode="gate_count",
    )

    print("\nRunning Interleaved‑XEB with x_axis_mode='gate_count'")
    res_gc = exp_gc.run(engine=engine, shots=4096, plot=True)

    # Keep figure open for inspection
    plt.show(block=True)

    print(f"[RESULT] CZ Gate Fidelity (gate_count) = {res_gc['gate_fidelity']:.6f}")
    print(f"[RESULT] CZ Gate Error (gate_count) = {res_gc['gate_error']:.6e}")

# ---------------------------------------------------------------------------
# 3. Four‑Qubit Standard XEB
# ---------------------------------------------------------------------------
def four_qubit_xeb_demo(engine: QuantumEngine) -> None:
    """Run a 4‑qubit standard XEB fidelity‑decay benchmark."""
    print("\n" + "=" * 70)
    print(" [4‑Qubit] Standard XEB Decay Benchmark ".center(70, "="))
    print("=" * 70)

    xeb_exp = StandardXEBExperiment(
        qubits=[0, 1, 2, 3],
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        x_axis_mode="depth",
    )

    res = xeb_exp.run(engine=engine, shots=SHOTS, plot=True, debug=False)
    plt.close("all")

    epc = res["xeb_analysis"]["fit_results"]["epc"]
    print(f"[RESULT] 4‑Qubit XEB EPC ≈ {epc:.4e}")

    schema = XEBAnalysisResult(
        qubits=[0, 1, 2, 3],
        axis_mode="depth",
        depths=list(res["xeb_analysis"]["raw_data"].keys()),
        mean_fidelity=list(res["xeb_analysis"]["raw_data"].values()),
        fit=res["xeb_analysis"]["fit_results"],
    )

    metadata = {
        "Experiment Type": "Standard‑XEB‑4Q",
        "Qubits": [0, 1, 2, 3],
        "Depths": DEPTHS,
    }
    generate_reports(schema, metadata)

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Entry point for the full 1Q + 2Q‑CZ Interleaved + 4Q XEB demo."""
    print("\n" + "=" * 74)
    print(" 1Q + 2Q‑CZ Interleaved + 4Q XEB Benchmark Demo (EGM v5.1.4) ".center(74, "="))
    print("=" * 74)

    engine = init_engine()

    single_qubit_xeb_demo(engine)
    two_qubit_interleaved_demo(engine)
    four_qubit_xeb_demo(engine)

    print("\n" + "=" * 74)
    print(" Demo Completed Successfully ".center(74, "="))
    print("=" * 74)

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    matplotlib.use("TkAgg")
    main()