# =============================================================================
# File   : examples/nzzs_demos/rb_xeb_q1_8qubits.py
# Version: v5.6 – 8-Qubit Single-Qubit RB + XEB Demo (EGM-consistent)
# =============================================================================

from __future__ import annotations
import logging
import argparse
import matplotlib
import matplotlib.pyplot as plt

# -------------------------------------------------------------------
# Framework Imports
# -------------------------------------------------------------------
from egm.core.engine.executor import QuantumEngine
from egm.core.backends.dummy_backend import DummyBackend
from egm.core.backends.dummy_backend_xeb import DummyBackend as XEBDummyBackend

from egm.core.experiments.benchmarking.rb import StandardRBExperiment
from egm.core.experiments.benchmarking.xeb import StandardXEBExperiment

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# -------------------------------------------------------------------
# Global parameters
# -------------------------------------------------------------------
SEED = 2026
SHOTS_RB = 8096
SHOTS_XEB = 8096

DEPTHS_RB = [0, 4, 8, 16, 32]
DEPTHS_XEB = [0, 4, 8, 16, 32]

CIRCUITS_PER_DEPTH = 30

# -------------------------------------------------------------------
# Engine initialization
# -------------------------------------------------------------------
def init_rb_engine() -> QuantumEngine:
    """RB uses the standard DummyBackend (NO parameters)."""
    backend = DummyBackend()
    return QuantumEngine(backend=backend)


def init_xeb_engine() -> QuantumEngine:
    """XEB uses the dedicated DummyBackend_XEB."""
    backend = XEBDummyBackend(
        cycle_fidelity=0.9985,
        noise_strength=0.9,
        jitter_scale=0.0001,
    )
    return QuantumEngine(backend=backend)

# -------------------------------------------------------------------
# Demo Entry
# -------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="8-Qubit Single-Qubit RB + XEB Demo (EGM-consistent)"
    )
    parser.parse_args()

    print("\n" + "=" * 80)
    print(" 8-Qubit Single-Qubit Benchmarking Demo (RB + XEB)")
    print("=" * 80)

    rb_engine = init_rb_engine()
    xeb_engine = init_xeb_engine()

    rb_epc = {}
    xeb_epc = {}

    for q in range(8):
        print("\n" + "-" * 70)
        print(f" Qubit {q}: Single-Qubit RB + XEB")
        print("-" * 70)

        # ------------------------------------------------------------
        # [1] Single-Qubit Standard RB
        # ------------------------------------------------------------
        rb_exp = StandardRBExperiment(
            qubits=[q],
            depths=DEPTHS_RB,
            circuits_per_depth=CIRCUITS_PER_DEPTH,
            seed=SEED,
        )

        rb_res = rb_exp.run(
            engine=rb_engine,
            shots=SHOTS_RB,
            plot=False,
        )

        rb_epc[q] = rb_res["rb_fit"]["epc"]
        print(f"[RB ] EPC = {rb_epc[q]:.3e}")

        # ------------------------------------------------------------
        # [2] Single-Qubit Standard XEB
        # ------------------------------------------------------------
        xeb_exp = StandardXEBExperiment(
            qubits=[q],
            depths=DEPTHS_XEB,
            circuits_per_depth=CIRCUITS_PER_DEPTH,
            x_axis_mode="depth",
        )

        xeb_res = xeb_exp.run(
            engine=xeb_engine,
            shots=SHOTS_XEB,
            plot=False,
            debug=False,
        )

        xeb_epc[q] = xeb_res["xeb_analysis"]["fit_results"]["epc"]
        print(f"[XEB] EPC = {xeb_epc[q]:.3e}")

    # ================================================================
    # Summary
    # ================================================================
    print("\n" + "=" * 80)
    print(" Summary: Single-Qubit EPC (RB vs XEB)")
    print("=" * 80)

    print(f"{'Qubit':>6} | {'RB EPC':>12} | {'XEB EPC':>12}")
    print("-" * 40)

    for q in range(8):
        print(
            f"{q:>6} | "
            f"{rb_epc[q]:>12.3e} | "
            f"{xeb_epc[q]:>12.3e}"
        )

    print("=" * 80)
    plt.show()


# -------------------------------------------------------------------
if __name__ == "__main__":
    matplotlib.use("TkAgg")
    main()