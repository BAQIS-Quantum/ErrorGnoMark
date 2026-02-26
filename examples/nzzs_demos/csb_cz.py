# =============================================================================
# File    : examples/new-demos/csb_cz_enhanced_demo.py
# Version : v1.3 – CZ Enhanced CSB Demo (Split-Estimation)
# =============================================================================
"""
CZ Gate Enhanced Channel Spectrum Benchmarking (CSB) Demo.

Features:
  - Enhanced CSB (Ox / Oy)
  - Dominant-spectral phase estimation
  - Infidelity inferred from decay under isotropic PTM assumption
  - Known target phase (calibration / validation use-case)
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

# -------------------------------------------------------------------
# Framework imports
# -------------------------------------------------------------------
try:
    from egm.core.engine.executor import QuantumEngine
    from egm.core.backends.dummy_backend_cphase_csb import DummyBackend
    from egm.core.experiments.benchmarking.csb_cz_enhanced import (
        CZEnhancedCSBExperiment,
    )
    from egm.schemas.results.csb import CSBAnalysisResult
    from egm.reporting.generators.terminal_generator import (
        generate_terminal_report,
    )
    from egm.reporting.generators.html_generator import HTMLReportGenerator
except ImportError as e:
    print(f"[ImportError] {e}")
    print("Ensure ErrorGnoMark is installed correctly (pip install -e .)")
    raise SystemExit(1)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def init_engine(
    cz_phase: float = 0.3,
    ptm_decay: float = 0.97,
    seed: int = 42,
) -> QuantumEngine:
    """
    Initialize the demo backend.

    ptm_decay is interpreted as the average non-identity PTM eigenvalue
    magnitude.
    """
    backend = DummyBackend(
        cz_phase=cz_phase,
        decay_rate=ptm_decay,
        seed=seed,
    )
    return QuantumEngine(backend=backend)


def generate_reports(result: CSBAnalysisResult, metadata: dict) -> None:
    generate_terminal_report(
        analysis_results=[result],
        experiment_params=metadata,
    )

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    template_dir = Path("src/egm/reporting/templates/html")
    html_gen = HTMLReportGenerator(template_dir=template_dir)

    html_path = reports_dir / f"csb_cz_enhanced_{result.plan_id}.html"

    if hasattr(html_gen, "generate_csb_report"):
        html_gen.generate_csb_report(result=result, output_path=html_path)
        print(f"[Report] HTML saved to: {html_path.resolve()}")
    else:
        print("[Report] No compatible HTML generator found.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CZ Gate Enhanced CSB Demo (Split-Estimation)"
    )
    parser.add_argument(
        "--target-phase",
        type=float,
        default=0.3,
        help="Target CZ phase in radians",
    )
    args = parser.parse_args()

    seed = 42
    depths = [2, 4, 8, 16, 32,40]
    circuits_per_depth = 30

    print("\n" + "=" * 70)
    print(" CZ Gate Enhanced CSB Demo (Split-Estimation)")
    print(f" Target phase = {args.target_phase:.6f} rad")
    print("=" * 70)

    engine = init_engine(cz_phase=args.target_phase)

    experiment = CZEnhancedCSBExperiment(
        qubits=[0, 1],
        depths=depths,
        circuits_per_depth=circuits_per_depth,
        rep=1,
        seed=seed,
        target_phase=args.target_phase,
    )

    print("\n[1/1] Running CZ Enhanced CSB Experiment ...")
    result: CSBAnalysisResult = experiment.run(backend=engine)
    print("[Result] CZ Enhanced CSB execution complete.")

    print("\n--- Extracted CSB Metrics ---")
    print(f"Status                : {result.status}")
    print(f"Extracted phase (φ)   : {result.phase}")
    print(f"Phase error           : {result.phase_error}")
    print(f"Stochastic infidelity : {result.stochastic_infidelity}")
    print(f"Process infidelity    : {result.process_infidelity}")

    metadata = {
        "Workflow": "CZ Enhanced CSB Demo (Split-Estimation)",
        "Gate": "CZ",
        "Qubits": experiment.qubits,
        "Depths": experiment.depths,
        "Circuits per Depth": circuits_per_depth,
        "Seed": seed,
        "Target Phase": args.target_phase,
        "Infidelity Model": "isotropic PTM (assumption-based)",
    }

    generate_reports(result, metadata)

    print("\n" + "=" * 70)
    print(" CZ Enhanced CSB Demo Completed ")
    print("=" * 70)


if __name__ == "__main__":
    main()