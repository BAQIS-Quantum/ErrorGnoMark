# =============================================================================
# File   : examples/nzzs_demos/rb_xeb_cz_q2_pairs.py
# Version: v5.8 – 2-Qubit CZ Interleaved RB + XEB Demo (Local-XEB Fixed)
# =============================================================================
"""
2-Qubit Interleaved Benchmarking Demo (RB + XEB, CZ Gate)

For each 2-qubit pair, this demo runs:
    1) Interleaved Randomized Benchmarking (IRB) on physical qubits
    2) Interleaved Cross-Entropy Benchmarking (IXEB) in LOCAL 2-qubit frame

NOTE:
    XEB is executed in a logical 2-qubit subspace [0, 1].
    This is required by the current DummyBackend_XEB design and is
    also the standard experimental practice.
"""

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

from egm.core.experiments.benchmarking.rb import InterleavedRBExperiment
from egm.core.experiments.benchmarking.xeb import InterleavedXEBExperiment
from egm.core.circuits.circuit import Gate

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

# Physical 2-qubit pairs
QUBIT_PAIRS = [
    (0, 1),
    (2, 3),
    (4, 5),
    (6, 7),
]

# -------------------------------------------------------------------
# Engine initialization
# -------------------------------------------------------------------
def init_rb_engine() -> QuantumEngine:
    """RB backend (standard DummyBackend)."""
    return QuantumEngine(backend=DummyBackend())


def init_xeb_engine() -> QuantumEngine:
    """XEB backend (UnifiedMatrixBackend)."""
    backend = XEBDummyBackend(
        cycle_fidelity=0.9985,
        noise_strength=0.9,
        two_qubit_boost=6.0,
        jitter_scale=0.0001,
    )
    return QuantumEngine(backend=backend)

# -------------------------------------------------------------------
# Demo Entry
# -------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="2-Qubit CZ Interleaved RB + XEB Demo (Local XEB Frame)"
    )
    parser.parse_args()

    print("\n" + "=" * 80)
    print(" 2-Qubit CZ Interleaved Benchmarking Demo (RB + XEB)")
    print("=" * 80)

    rb_engine = init_rb_engine()
    xeb_engine = init_xeb_engine()

    rb_results = {}
    xeb_results = {}

    # ================================================================
    # Loop over physical qubit pairs
    # ================================================================
    for q0, q1 in QUBIT_PAIRS:
        pair_label = f"{q0}-{q1}"

        print("\n" + "-" * 70)
        print(f" Qubit Pair {pair_label}: CZ Interleaved RB + XEB")
        print("-" * 70)

        # ============================================================
        # [1] Interleaved RB (PHYSICAL qubits)
        # ============================================================
        phys_cz_gate = Gate("cz", qubits=(q0, q1))

        irb_exp = InterleavedRBExperiment(
            qubits=[q0, q1],
            interleaved_gate=phys_cz_gate,
            depths=DEPTHS_RB,
            circuits_per_depth=CIRCUITS_PER_DEPTH,
            seed=SEED,
        )

        irb_res = irb_exp.run(
            engine=rb_engine,
            shots=SHOTS_RB,
            plot=False,
        )

        rb_results[pair_label] = {
            "epg": irb_res["epg"],
            "fidelity": irb_res["fidelity"],
        }

        print(
            f"[IRB ] CZ Fidelity = {irb_res['fidelity']:.6f}, "
            f"EPG = {irb_res['epg']:.3e}"
        )

        # ============================================================
        # [2] Interleaved XEB (LOCAL 2-QUBIT FRAME)
        # ============================================================
        # IMPORTANT: XEB must run in logical frame [0, 1]
        local_qubits = [0, 1]
        local_cz_gate = Gate("cz", qubits=(0, 1))

        ixeb_exp = InterleavedXEBExperiment(
            qubits=local_qubits,
            interleaved_gate=local_cz_gate,
            depths=DEPTHS_XEB,
            circuits_per_depth=CIRCUITS_PER_DEPTH,
            seed=SEED,
            x_axis_mode="gate_count",
        )

        ixeb_res = ixeb_exp.run(
            engine=xeb_engine,
            shots=SHOTS_XEB,
            plot=False,
        )

        xeb_results[pair_label] = {
            "gate_fidelity": ixeb_res["gate_fidelity"],
            "gate_error": ixeb_res["gate_error"],
        }

        print(
            f"[IXEB] CZ Fidelity = {ixeb_res['gate_fidelity']:.6f}, "
            f"Gate Error = {ixeb_res['gate_error']:.3e}"
        )

    # ================================================================
    # Summary
    # ================================================================
    print("\n" + "=" * 80)
    print(" Summary: 2-Qubit CZ Gate (IRB vs Interleaved-XEB)")
    print("=" * 80)

    print(
        f"{'Pair':>8} | {'IRB EPG':>12} | {'IRB Fid':>10} | "
        f"{'XEB Err':>12} | {'XEB Fid':>10}"
    )
    print("-" * 70)

    for pair in rb_results:
        print(
            f"{pair:>8} | "
            f"{rb_results[pair]['epg']:>12.3e} | "
            f"{rb_results[pair]['fidelity']:>10.6f} | "
            f"{xeb_results[pair]['gate_error']:>12.3e} | "
            f"{xeb_results[pair]['gate_fidelity']:>10.6f}"
        )

    print("=" * 80)
    plt.show()


# -------------------------------------------------------------------
if __name__ == "__main__":
    matplotlib.use("TkAgg")
    main()