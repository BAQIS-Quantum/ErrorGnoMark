# File: examples/new-demos/RB_demo_1q2q_dashboard.py
# ---------------------------------------------------------------
# Example: End-to-End Randomized Benchmarking (RB) Workflow Demo
# ---------------------------------------------------------------
# [UPDATED] Passes exact node coordinates to Dashboard.
# ---------------------------------------------------------------

import logging
import pandas as pd
from uuid import uuid4
from pathlib import Path
from typing import List

# --- Framework Imports ---
try:
    from egm.core.experiments.benchmarking.rb import StandardRBExperiment
    from egm.core.engine.executor import QuantumEngine
    from egm.core.backends.dummy_backend import DummyBackend
    from egm.schemas.results.rb import RBAnalysisResult, RBSequenceDataPoint
    from egm.schemas.results.base import FitResult, FitParameter

    # Reporting Imports
    from egm.reporting.generators.html_generator import HTMLReportGenerator
    from egm.reporting.dashboard_generator import HTMLDashboard

    # Resource Selector & Internal Helpers
    from egm.core.data.hardware.topology_selector import (
        interactive_select_resources,
        _resolve_csv_path,
        _parse_connectivity_with_values,
        _extract_qubit_metrics,
        _get_chip_layout_params,
        _generate_node_coordinates  # [NEW] Import coordinate generator
    )

    import egm
except ImportError as e:
    print(f"ImportError: {e}")
    exit(1)

# Configure global logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def run_rb_and_add_to_dashboard(
        engine: QuantumEngine,
        dashboard: HTMLDashboard,
        qubits: List[int],
        depths: List[int],
        circuits_per_depth: int,
        shots: int,
        seed: int
):
    """Helper function to configure, run, and report a single RB experiment."""
    print(f"\n--- Running Automated RB for Qubits {qubits} ---")
    rb_exp = StandardRBExperiment(qubits=qubits, depths=depths, circuits_per_depth=circuits_per_depth, seed=seed)
    results_dict = rb_exp.run(engine=engine, shots=shots, plot=False)

    if results_dict and results_dict.get("fit_successful"):
        params = results_dict.get("params", {})
        param_errs = results_dict.get("param_errors", {})
        if not params: params = {k: results_dict.get(k) for k in ["A", "p", "B"]}

        fit_obj = FitResult(
            model_name="rb_exponential_decay",
            params=[
                FitParameter(name="A", value=params.get("A"), std_dev=param_errs.get("A")),
                FitParameter(name="p", value=params.get("p"), std_dev=param_errs.get("p")),
                FitParameter(name="B", value=params.get("B"), std_dev=param_errs.get("B")),
            ],
        )

        result_obj = RBAnalysisResult(
            analyzer_version="2.2",
            qubits=rb_exp.qubits,
            plan_id=uuid4(),
            result_id=str(uuid4()),
            raw_data_ids=[uuid4() for _ in rb_exp.depths],
            tags=["automated_run", "batch_demo"],
            notes=f"Automated run for qubits {qubits}.",
            success=results_dict["fit_successful"],
            fit=fit_obj,
            depths=results_dict["x_data"],
            means=results_dict["y_data"],
            stds=results_dict["y_err"],
            sequence_data=[
                RBSequenceDataPoint(sequence_length=int(x), survival_probability=float(y), std_error=float(err))
                for x, y, err in
                zip(results_dict["x_data"], results_dict["y_data"], results_dict["y_err"])
            ],
        )
        dashboard.add_experiments([result_obj])
        print(f"-> Success: EPC = {results_dict.get('epc', 0):.4e}. Added to Dashboard.")
        return True
    else:
        print(f"-> Failed: Fit unsuccessful for qubits {qubits}.")
        return False


def main() -> None:
    DEMO_SEED = 42
    CHIP_NAME = "Baihua"  # Target Chip

    print(f"\n--- EGM RB Batch Demo Workflow (Chip: {CHIP_NAME}) ---")

    # 1. Setup Dashboard
    package_root = Path(egm.__file__).parent
    template_path = package_root / "reporting" / "templates" / "html"
    html_gen = HTMLReportGenerator(template_dir=template_path)
    dashboard_dir = Path("reports_dashboard")

    dashboard = HTMLDashboard(
        generator=html_gen,
        output_dir=dashboard_dir,
        title=f"Quantum Error Dashboard - {CHIP_NAME}"
    )

    selection_save_dir = dashboard_dir / "selections"
    backend = DummyBackend(clifford_fidelity=0.985, spam_error_rate=0.0005)
    engine = QuantumEngine(backend=backend)

    # 2. [UPDATED] Extract Full Topology Info (Matches Resource Selector UI)
    print("\n[Init] Loading Full Chip Topology...")
    try:
        # Resolve CSV
        csv_path = _resolve_csv_path(CHIP_NAME, None)
        df = pd.read_csv(csv_path)

        # Extract Data
        full_edge_data = _parse_connectivity_with_values(df)
        full_qubit_data = _extract_qubit_metrics(df)

        # Calculate Layout Shape & Coordinates
        layout_info = _get_chip_layout_params(CHIP_NAME, len(full_qubit_data))

        # [NEW] Generate coordinates exactly like the UI
        node_coords = _generate_node_coordinates(layout_info['type'], layout_info['rows'], layout_info['cols'])

        all_physical_qubits = sorted(list(full_qubit_data.keys()))
        all_physical_edges = sorted(list(full_edge_data.keys()))

        print(f"       Loaded {len(all_physical_qubits)} qubits, {len(all_physical_edges)} edges.")

    except Exception as e:
        print(f"[Warning] Failed to load full topology: {e}. Using fallback.")
        all_physical_qubits = list(range(12 * 13))
        all_physical_edges = []
        node_coords = None

    # 3. Interactive Selection
    print("\n" + "=" * 70)
    print(" Phase 0: Interactive Target Selection ")
    print("=" * 70)

    selected_qubits, selected_edges, _ = interactive_select_resources(
        chip_name=CHIP_NAME,
        title=f"Select Qubits ({CHIP_NAME} Layout)",
        export_prefix="demo_selection",
        save_dir=selection_save_dir
    )

    # 4. [CRITICAL] Pass explicit node coordinates to Dashboard
    dashboard.set_topology(
        qubits=all_physical_qubits,
        edges=all_physical_edges,
        node_coords=node_coords  # [NEW] Pass coordinates
    )

    # Parse Selection
    qubit_sets_1q = [[q] for q in selected_qubits]
    qubit_sets_2q = [list(edge) for edge in selected_edges]

    if not qubit_sets_1q and not qubit_sets_2q:
        print("\n[!] No qubits selected. Using fallback.")
        qubit_sets_1q = [[0], [1]]

    # 5. Batch Run
    print("\n" + "=" * 70)
    print(" Part 1: Automated Batch Workflow ")
    print("=" * 70)

    all_target_sets = qubit_sets_1q + qubit_sets_2q
    for i, q_set in enumerate(all_target_sets):
        run_rb_and_add_to_dashboard(
            engine=engine, dashboard=dashboard, qubits=q_set,
            depths=[2, 8, 16, 32], circuits_per_depth=10, shots=4096, seed=DEMO_SEED + i
        )

    # 6. Save
    print("\n" + "=" * 70)
    print(" Saving Dashboard ")
    print("=" * 70)
    index_path = dashboard.save("RB_Results.html")
    print(f"\n[Success] Dashboard at: {index_path}")
    print("Open it to see the Interactive Topology Map!")


if __name__ == "__main__":
    main()