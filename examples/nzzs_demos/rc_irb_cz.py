# =============================================================================
# File   : examples/new-demos/irb_rc_comparison_demo.py
# Version: v5.2 – Interleaved RB vs RB+RC Demo (CZ Gate)
# Author : OpenAI‑Assistant
# =============================================================================
"""
Interleaved Randomized Benchmarking (IRB) Demo with RC Comparison

This demo runs TWO experiments:
    1) Standard Interleaved RB (CZ gate, no RC)
    2) Interleaved RB + Randomized Compiling (CZ gate)

Purpose:
    • Diagnose coherent vs stochastic error contributions
    • Demonstrate RB + RC workflow consistency
    • Provide apples-to-apples IRB comparison
"""

from __future__ import annotations
import logging
from pathlib import Path
import argparse
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

# -------------------------------------------------------------------
# Framework Imports
# -------------------------------------------------------------------
try:
    # Engine / backend
    from egm.core.engine.executor import QuantumEngine
    from egm.core.backends.dummy_backend import DummyBackend

    # Experiments
    from egm.core.experiments.benchmarking.rb import (
        InterleavedRBExperiment,
        RBCompilationOptions,
    )

    # Circuit objects
    from egm.core.circuits.circuit import Gate

    # Schema / reporting
    from egm.schemas.results.rb import RBAnalysisResult
    from egm.reporting.generators.terminal_generator import generate_terminal_report

except ImportError as e:
    print(f"[ImportError] {e}")
    print("Ensure ErrorGnoMark is installed correctly (pip install -e .)")
    exit(1)

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# -------------------------------------------------------------------
# Helper
# -------------------------------------------------------------------
def init_engine(
    clifford_fidelity: float = 0.985,
    spam_err: float = 5e-4,
) -> QuantumEngine:
    backend = DummyBackend(
        clifford_fidelity=clifford_fidelity,
        spam_error_rate=spam_err,
    )
    return QuantumEngine(backend=backend)


# -------------------------------------------------------------------
# Demo Entry
# -------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Interleaved RB vs RB+RC Demo (CZ gate)"
    )
    args = parser.parse_args()

    SEED = 2026
    SHOTS = 8096
    DEPTHS = [0, 4, 8, 16, 32]
    CIRCUITS_PER_DEPTH = 30

    print("\n" + "=" * 80)
    print(" Interleaved RB Demo: CZ gate (No RC  vs  With RC)")
    print("=" * 80)

    engine = init_engine()

    # ================================================================
    # Experiment configuration
    # ================================================================
    cz_gate = Gate("cz", [0, 1])

    # ================================================================
    # [1] Interleaved RB — NO RC
    # ================================================================
    print("\n[1/2] Running Interleaved RB (CZ, RC = OFF)")

    irb_no_rc = InterleavedRBExperiment(
        qubits=[0, 1],
        interleaved_gate=cz_gate,
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        seed=SEED,
        rb_compilation=None,  # ✅ No RC
    )

    res_no_rc = irb_no_rc.run(
        engine=engine,
        shots=SHOTS,
        plot=True,
    )

    print("[Result] Interleaved RB (no RC) complete.")

    # ================================================================
    # [2] Interleaved RB — WITH RC
    # ================================================================
    print("\n[2/2] Running Interleaved RB (CZ, RC = ON)")

    irb_rc = InterleavedRBExperiment(
        qubits=[0, 1],
        interleaved_gate=cz_gate,
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        seed=SEED,
        rb_compilation=RBCompilationOptions(
            scheme="RC",
            seed=SEED,
        ),
    )

    res_rc = irb_rc.run(
        engine=engine,
        shots=SHOTS,
        plot=True,
    )

    print("[Result] Interleaved RB + RC complete.")

    # ================================================================
    # Optional: Terminal comparison summary
    # ================================================================
    print("\n" + "-" * 70)
    print(" Summary (CZ Gate Interleaved RB)")
    print("-" * 70)

    print(f" No RC  - Fidelity : {res_no_rc['fidelity']:.6f}")
    print(f" With RC - Fidelity : {res_rc['fidelity']:.6f}")

    print(f" No RC  - EPG      : {res_no_rc['epg']:.3e}")
    print(f" With RC - EPG      : {res_rc['epg']:.3e}")

    print("-" * 70)

    # Keep figures open
    plt.show()


# -------------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------------
if __name__ == "__main__":
    main()