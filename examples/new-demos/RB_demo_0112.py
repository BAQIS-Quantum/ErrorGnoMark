# File: examples/new-demos/RB_demo_0112.py
# -------------------------------------------------------------------
# Module: Comprehensive Randomized Benchmarking (RB) Demo Suite
# -------------------------------------------------------------------
# This script demonstrates the full capabilities of the modular RB
# architecture in ErrorGnoMark, covering the full spectrum from
# manual functional composition to automated class-based orchestration.
#
# Scenarios Covered:
#   0. Logical vs Physical Layers (Decomposition Visualization)
#   1. Standard Single-Qubit (1Q) RB (Respective Execution)
#   2. Standard Two-Qubit (2Q) RB (Respective Execution)
#   3. Simultaneous 1Q RB (Parallel execution on disjoint qubits)
#   4. Simultaneous 2Q RB (Parallel execution on disjoint pairs)
#   5. Interleaved RB (Functional API: Manual Control)
#   6. Interleaved RB (Class API: Automated Orchestration)
#
# COMPATIBILITY: Architecture v5.4 (Unified Run Pipeline)
# -------------------------------------------------------------------

import logging
import os
from pathlib import Path
import numpy as np
from typing import List, Dict, Any

# --- Framework Imports ---
try:
    from egm.core.engine.executor import QuantumEngine
    from egm.core.backends.dummy_backend import DummyBackend
    from egm.core.circuits.circuit import QuantumCircuit, Gate

    # RB Module Imports
    from egm.core.experiments.benchmarking.rb import (
        generate_single_standard_rb_circuit,
        generate_standard_rb_circuits,
        generate_simultaneously_standard_rb_circuits,
        generate_interleaved_rb_circuits,
        StandardRBExperiment,
        InterleavedRBExperiment
    )
    from egm.core.analysis.rb import (
        analyze_rb_standard,
        analyze_rb_simultaneous,
        calculate_epg
    )
    from egm.schemas.results.rb import RBAnalysisResult

    # Reporting Imports
    from egm.reporting.generators.html_generator import HTMLReportGenerator
    import egm

except ImportError as e:
    print(f"[ImportError] {e}\nPlease check EGM installation.")
    exit(1)

# Configure Logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# --- Global Configuration ---
SEED = 2025
SHOTS = 1024
DEPTHS = [2, 4, 8, 16, 32, 64]
CIRCUITS_PER_DEPTH = 5  # Kept small for rapid demonstration


# -------------------------------------------------------------------
# Helper Utilities
# -------------------------------------------------------------------
def init_engine():
    """Initialize a dummy backend with known error rates for validation."""
    # 1Q error ~ 0.1%, 2Q error ~ 1%
    backend = DummyBackend(clifford_fidelity=0.995, spam_error_rate=0.01)
    return QuantumEngine(backend=backend)


def print_separator(title: str):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def preview_circuit(qc: QuantumCircuit, title: str):
    """Helper to visualize circuit structure in the console."""
    print(f"\n--- Circuit Preview: {title} (Depth {qc.metadata.get('depth', 'N/A')}) ---")
    try:
        # Use the circuit's text drawing method
        qc.draw(style="text")
    except Exception:
        print(f"[Visualizer not available] Qubits: {qc.qubits}, Gates: {len(qc.gates)}")
    print("-" * 40 + "\n")


def stitch_data(circuits: List[QuantumCircuit], engine_results: List) -> List[Dict[str, Any]]:
    """
    Manual Data Stitching Helper for Functional API demos.

    [Architecture Note]
    In the Functional API approach, the user is responsible for mapping
    the raw execution results (counts) back to the circuit metadata (depth).
    This function performs that bridging.

    Args:
        circuits: List of executed circuits containing metadata.
        engine_results: List of (ideal, counts) tuples from engine execution.

    Returns:
        List of dicts: [{"data": counts, "metadata": meta}, ...] ready for analysis.
    """
    stitched = []
    for circ, res_tuple in zip(circuits, engine_results):
        # res_tuple[0] is ideal_probs (unused), res_tuple[1] is noisy_counts
        stitched.append({
            "data": res_tuple[1],
            "metadata": circ.metadata
        })
    return stitched


def print_analysis_result(res: RBAnalysisResult, label: str):
    """Formatted console output for analysis results."""
    if res.success:
        # Extract 'p' parameter from the fit model
        p_val = next((p.value for p in res.fit.params if p.name == 'p'), 0)
        # Calculate Error Per Clifford (EPC)
        d = 2 ** len(res.qubits)
        epc = ((d - 1) / d) * (1 - p_val)

        print(f">>> {label} Results:")
        print(f"    Fit Success:    True")
        print(f"    Decay Rate (p): {p_val:.5f}")
        print(f"    Est. EPC:       {epc:.5e}")
    else:
        print(f">>> {label} Failed: {res.error_message}")


# -------------------------------------------------------------------
# Main Execution Flow
# -------------------------------------------------------------------
def main():
    engine = init_engine()

    # =================================================================
    # Part 0: Logic vs Physics (Decomposition Demo)
    # Demonstrates how Abstract Clifford gates become Physical Gates
    # =================================================================
    print_separator("Part 0: Logic vs Physics (Decomposition Demo)")

    # 1. Generate Logical Circuit (Abstract Clifford Gates)
    demo_depth = 2
    print(f"-> Generating Logical RB Circuit (Depth {demo_depth})...")

    # We deliberately create a circuit WITHOUT physical decomposition first
    logic_demo = generate_single_standard_rb_circuit(
        qubits=[0],
        depth=demo_depth,
        seed=SEED,
        # Native gates are None, so output is abstract (H, S, etc.)
        native_gates=None
    )
    preview_circuit(logic_demo, "Logical Circuit (Abstract Gates)")

    # 2. Decompose into Physical Basis
    # Simulating a Rigetti-like basis: ['rx', 'rz', 'cz']
    demo_basis = ['rx', 'rz', 'cz']
    # TODO 若不补充XYZ门分解，使用'ibm'会报错缺少Y门，请柴老师再确认一下
    print(f"-> Decomposing into basis: {demo_basis}...")

    # [API Usage]: Direct string list passing to decompose
    phys_demo = logic_demo.decompose(basis_gates=demo_basis)
    phys_demo.measure_all()  # Add measurement for completeness

    preview_circuit(phys_demo, f"Decomposed Physical Circuit")

    # =================================================================
    # Part 1: Standard 1Q RB (Respective / Isolated)
    # Functional API usage: Generate -> Execute -> Stitch -> Analyze
    # =================================================================
    print_separator("Part 1: Standard Single-Qubit (1Q) RB")
    target_1q = [0]

    # 1. Generate
    # Note: with_measurement=True is default, ensuring measure gates exist
    print(f"-> Generating 1Q circuits for Qubit {target_1q}...")
    circuits_1q = generate_standard_rb_circuits(
        qubits=target_1q,
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        seed=SEED,
        native_gates=None  # Use ideal gates for this demo part
    )

    # 2. Preview
    if circuits_1q:
        preview_circuit(circuits_1q[-1], "Standard 1Q Sample")

    # 3. Execute
    print(f"-> Executing {len(circuits_1q)} circuits...")
    raw_res_1q = engine.execute_with_ideal(circuits_1q, shots=SHOTS)

    # 4. Stitch Data (Manual Step in Functional API)
    stitched_1q = stitch_data(circuits_1q, raw_res_1q)

    # 5. Analyze
    fit_1q = analyze_rb_standard(stitched_1q)
    print_analysis_result(fit_1q, "Standard 1Q")

    # =================================================================
    # Part 2: Standard 2Q RB (Respective / Isolated)
    # =================================================================
    print_separator("Part 2: Standard Two-Qubit (2Q) RB")
    target_2q = [0, 1]

    # 1. Generate
    print(f"-> Generating 2Q circuits for Qubits {target_2q}...")
    circuits_2q = generate_standard_rb_circuits(
        qubits=target_2q,
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        seed=SEED + 1
    )

    # 2. Preview
    if circuits_2q:
        preview_circuit(circuits_2q[CIRCUITS_PER_DEPTH], "Standard 2Q Sample")

    # 3. Execute
    print(f"-> Executing {len(circuits_2q)} circuits...")
    raw_res_2q = engine.execute_with_ideal(circuits_2q, shots=SHOTS)

    # 4. Stitch & Analyze
    stitched_2q = stitch_data(circuits_2q, raw_res_2q)
    fit_2q = analyze_rb_standard(stitched_2q)
    print_analysis_result(fit_2q, "Standard 2Q")

    # =================================================================
    # Part 3: Simultaneous 1Q RB
    # Running Q0 and Q1 RB sequences in PARALLEL circuits
    # =================================================================
    print_separator("Part 3: Simultaneous 1Q RB (Q0 || Q1)")

    # Disjoint 1Q groups
    groups_simul_1q = [[0], [1]]

    # 1. Generate (Returns Dict[Depth, List[Circuit]])
    print(f"-> Generating simultaneous circuits for groups {groups_simul_1q}...")
    simul_map_1q = generate_simultaneously_standard_rb_circuits(
        qubit_groups=groups_simul_1q,
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        same_per_qubit=True,  # Use same random sequence pattern for fairness
        seed=SEED + 2
    )

    # Flatten dict to list for execution
    circuits_simul_1q = []
    for d in DEPTHS:
        circuits_simul_1q.extend(simul_map_1q[d])

    # 2. Preview
    if circuits_simul_1q:
        preview_circuit(simul_map_1q[DEPTHS[-1]][0], "Simultaneous 1Q (Q0 || Q1)")

    # 3. Execute
    print(f"-> Executing {len(circuits_simul_1q)} simultaneous circuits...")
    raw_res_simul_1q = engine.execute_with_ideal(circuits_simul_1q, shots=SHOTS)

    # 4. Stitch & Analyze
    # Note: analyze_rb_simultaneous auto-infers groups from circuit metadata
    stitched_simul_1q = stitch_data(circuits_simul_1q, raw_res_simul_1q)
    results_dict_1q = analyze_rb_simultaneous(stitched_simul_1q)

    for g_tuple, schema in results_dict_1q.items():
        print_analysis_result(schema, f"Simultaneous 1Q Group {list(g_tuple)}")

    # =================================================================
    # Part 4: Simultaneous 2Q RB
    # Running Q0-Q1 and Q2-Q3 RB sequences in PARALLEL circuits
    # =================================================================
    print_separator("Part 4: Simultaneous 2Q RB (Q0-Q1 || Q2-Q3)")

    # Disjoint 2Q pairs
    groups_simul_2q = [[0, 1], [2, 3]]

    # 1. Generate
    print(f"-> Generating simultaneous circuits for groups {groups_simul_2q}...")
    simul_map_2q = generate_simultaneously_standard_rb_circuits(
        qubit_groups=groups_simul_2q,
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        same_per_qubit=False,  # Use unique sequences for each pair
        seed=SEED + 3
    )

    circuits_simul_2q = []
    for d in DEPTHS:
        circuits_simul_2q.extend(simul_map_2q[d])

    # 2. Preview
    if circuits_simul_2q:
        preview_circuit(simul_map_2q[DEPTHS[1]][0], "Simultaneous 2Q (Q0-Q1 || Q2-Q3)")

    # 3. Execute
    print(f"-> Executing {len(circuits_simul_2q)} simultaneous circuits...")
    raw_res_simul_2q = engine.execute_with_ideal(circuits_simul_2q, shots=SHOTS)

    # 4. Stitch & Analyze
    stitched_simul_2q = stitch_data(circuits_simul_2q, raw_res_simul_2q)
    results_dict_2q = analyze_rb_simultaneous(stitched_simul_2q)

    for g_tuple, schema in results_dict_2q.items():
        print_analysis_result(schema, f"Simultaneous 2Q Group {list(g_tuple)}")

    # =================================================================
    # Part 5: Interleaved RB (Functional API)
    # Manual orchestration of Reference + Interleaved Batches
    # =================================================================
    print_separator("Part 5: 1Q Interleaved RB (Functional API)")
    target_irb_qubits = [0]
    target_gate = Gate("x", tuple(target_irb_qubits))  # Pauli-X on Qubit 0

    print(f"-> Target Gate: {target_gate.name} on {target_irb_qubits}")

    # 1. Generate Both Sets (Manual Calls)
    print("-> Generating Reference circuits...")
    c_ref = generate_standard_rb_circuits(
        qubits=target_irb_qubits,
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        seed=SEED + 10
    )

    print("-> Generating Interleaved circuits...")
    c_int = generate_interleaved_rb_circuits(
        qubits=target_irb_qubits,
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        seed=SEED + 10,
        interleaved_gate=target_gate
    )

    # 2. Preview
    if c_int:
        preview_circuit(c_int[-1], f"Interleaved with {target_gate.name}")

    # 3. Execute Both
    print("-> Executing Reference Batch...")
    raw_ref = engine.execute_with_ideal(c_ref, shots=SHOTS)
    print("-> Executing Interleaved Batch...")
    raw_int = engine.execute_with_ideal(c_int, shots=SHOTS)

    # 4. Stitch Both
    stitched_ref = stitch_data(c_ref, raw_ref)
    stitched_int = stitch_data(c_int, raw_int)

    # 5. Analyze & Compare
    fit_ref = analyze_rb_standard(stitched_ref)
    fit_int = analyze_rb_standard(stitched_int)

    if fit_ref.success and fit_int.success:
        p_ref = next(p.value for p in fit_ref.fit.params if p.name == 'p')
        p_int = next(p.value for p in fit_int.fit.params if p.name == 'p')
        epg = calculate_epg(p_ref, p_int, num_qubits=1)

        print(f">>> 1Q IRB Functional Results:")
        print(f"    Ref Decay (p): {p_ref:.5f}")
        print(f"    Int Decay (p): {p_int:.5f}")
        print(f"    Calculated EPG: {epg:.5e}")
    else:
        print(">>> 1Q IRB Functional Analysis Failed.")

    # =================================================================
    # Part 6: Interleaved RB (2Q - Functional API)
    # =================================================================
    print_separator("Part 6: 2Q Interleaved RB (Functional API)")
    target_irb_qubits_2q = [0, 1]
    target_gate_2q = Gate("cz", tuple(target_irb_qubits_2q))

    print(f"-> Target Gate: {target_gate_2q.name} on {target_irb_qubits_2q}")

    # 1. Generate
    c_ref_2q = generate_standard_rb_circuits(
        qubits=target_irb_qubits_2q,
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        seed=SEED + 20
    )
    c_int_2q = generate_interleaved_rb_circuits(
        qubits=target_irb_qubits_2q,
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        seed=SEED + 20,
        interleaved_gate=target_gate_2q
    )

    # 2. Execute
    raw_ref_2q = engine.execute_with_ideal(c_ref_2q, shots=SHOTS)
    raw_int_2q = engine.execute_with_ideal(c_int_2q, shots=SHOTS)

    # 3. Stitch & Analyze
    stitched_ref_2q = stitch_data(c_ref_2q, raw_ref_2q)
    stitched_int_2q = stitch_data(c_int_2q, raw_int_2q)

    fit_ref_2q = analyze_rb_standard(stitched_ref_2q)
    fit_int_2q = analyze_rb_standard(stitched_int_2q)

    if fit_ref_2q.success and fit_int_2q.success:
        p_ref = next(p.value for p in fit_ref_2q.fit.params if p.name == 'p')
        p_int = next(p.value for p in fit_int_2q.fit.params if p.name == 'p')
        epg = calculate_epg(p_ref, p_int, num_qubits=2)

        print(f">>> 2Q IRB Functional Results:")
        print(f"    Ref Decay (p): {p_ref:.5f}")
        print(f"    Int Decay (p): {p_int:.5f}")
        print(f"    Calculated EPG (CZ): {epg:.5e}")
    else:
        print(">>> 2Q IRB Functional Analysis Failed.")

    # =================================================================
    # Part 7: Interleaved RB (Class API)
    # Encapsulated workflow: Generation -> Execution -> Stitching -> Analysis
    # =================================================================
    print_separator("Part 7: Interleaved RB (Class API + HTML Report)")

    # 1. Initialize Experiment Configuration
    irb_exp = InterleavedRBExperiment(
        interleaved_gate=target_gate,
        qubits=target_irb_qubits,
        depths=DEPTHS,
        circuits_per_depth=CIRCUITS_PER_DEPTH,
        seed=SEED + 100
    )

    # 2. Run Pipeline (Generation -> Execution -> Stitching -> Analysis)
    # [Architecture Note]: In v5.3+, the .run() method is an all-in-one orchestrator.
    # It returns the final analysis results directly, eliminating the need for a separate .analyze() call.
    print("-> Running Experiment Class (Auto Generation & Stitching)...")
    result_dict = irb_exp.run(engine=engine, shots=SHOTS, plot=False)

    # 3. Report & Save HTML
    if result_dict["success"]:
        print(f"\n>>> IRB Class Results:")
        print(f"    Target Gate: {result_dict['gate_name']}")
        print(f"    Final EPG:   {result_dict['epg']:.5e}")

        # HTML Generation Logic
        try:
            package_root = Path(egm.__file__).parent
            template_path = package_root / "reporting" / "templates" / "html"
            html_gen = HTMLReportGenerator(template_dir=template_path)

            output_dir = Path("rb_reports")
            output_dir.mkdir(exist_ok=True)

            ref_path = output_dir / "irb_reference_report.html"
            int_path = output_dir / "irb_interleaved_report.html"

            print(f"\n-> Generating HTML Reports in '{output_dir}'...")
            html_gen.generate_rb_report(result_dict['fit_reference'], ref_path)
            html_gen.generate_rb_report(result_dict['fit_interleaved'], int_path)
            print(f"   Saved: {ref_path}")
            print(f"   Saved: {int_path}")

        except Exception as e:
            print(f"[Warning] Failed to generate HTML report: {e}")
    else:
        print(f">>> Experiment Failed: {result_dict.get('error')}")

    print("\n" + "=" * 60)
    print(" All Demos Completed Successfully ")
    print("=" * 60)


if __name__ == "__main__":
    main()