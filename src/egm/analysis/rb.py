# =============================================================================
# File: src/egm/core/analysis/rb.py
# Version: v5.4 – Robust Data Handling (Fixed Prob Truncation Issue)
# =============================================================================
"""
Randomized Benchmarking (RB) Analysis Utilities

This module provides the complete analysis stack for RB experiments:
1. Core Mathematics: Decay function models and curve fitting (`fit_rb_data`).
2. High-Level Analyzers: Functions that take stitched results (Data + Metadata)
   and return standardized Schema objects.
3. Metrics: EPG and EPC calculations.

Architectural Change v5.4:
- Improved data normalization logic to handle truncated probability distributions
  safely (avoiding artificial fidelity inflation).
"""

from __future__ import annotations

import numpy as np
import logging
import warnings
from uuid import uuid4
from typing import Dict, Any, List, Optional, Tuple, Sequence
from scipy.optimize import curve_fit, OptimizeWarning

# ---------------------------------------------------------------------
# Framework Imports
# ---------------------------------------------------------------------
from egm.schemas.results.base import FitResult, FitParameter
from egm.schemas.results.rb import RBAnalysisResult, RBSequenceDataPoint
from egm.circuits.circuit import QuantumCircuit

# ---------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# ---------------------------------------------------------------------
# Default Constants
# ---------------------------------------------------------------------
_MAX_EVALS = 10000
_DEFAULT_P_GUESS = 0.99


def stitch_rb_results(
        circuits: List[QuantumCircuit],
        execution_results: List[Tuple[Any, Any]]
) -> List[Dict[str, Any]]:
    """
    Combines circuit metadata with execution results into a standardized format.

    [Core Utility & Why we need it]
    -------------------------------
    Function: Data Structuring / Formatting.
    Use Case: This function acts as the bridge between the Executor (which returns raw counts)
              and the Analyzer (which requires metadata like 'depth' to fit curves).
              Exposing this allows users to manually stitch data if they run experiments externally
              (e.g., running on IBM/IonQ directly and feeding data back to EGM for analysis).

    Input Specification (Format & Compatibility):
    ---------------------------------------------
    1. Standard Engine Format:
       The `execution_results` argument strictly expects the format returned by
       `QuantumEngine.execute_with_ideal()`. This is a `List` of `Tuples`, where each tuple is:

           (ideal_probabilities, noisy_counts)

       - Index 0 (ideal_probabilities): Dictionary of ideal outcomes (e.g., `{'00': 1.0}`).
       - Index 1 (noisy_counts): Dictionary of actual experimental counts (e.g., `{'00': 98, '11': 2}`).

    2. External/Manual Data Compatibility:
       If you are importing data from an external source where ideal probabilities are unknown
       or irrelevant for RB, you can pass `None` in the first slot: `(None, noisy_counts)`.

       However, maintaining this Tuple structure ensures compatibility. If your workflow *does* require ideal data (e.g., for verifying Clifford correctness or debugging specific sequences),
       you can safely pass it in Index 0. This function preserves the structure so other EGM
       components can access that data if needed.

    Special Case: Simultaneous RB (Parallel Execution)
    --------------------------------------------------
    When preparing data for `analyze_rb_simultaneous`, the input format to this function
    is **exactly the same**, but the content must satisfy specific requirements:

    1. Circuits Metadata: The `circuits` list must contain a "groups" key in metadata
       (e.g., `metadata={"groups": [(0,), (1,)], "depth": 10}`). This tells the analyzer
       which qubits belong to which disjoint experiment.

    2. Global Counts: The `noisy_counts` in `execution_results` must cover the **full** combined system (e.g., for 2 parallel qubits, keys should be '00', '01', '10', '11').
       The analyzer will automatically handle the marginalization for each group.

    Args:
        circuits: The list of QuantumCircuit objects that were executed.
                  CRITICAL: Each circuit.metadata must contain keys required by the analyzer
                  (e.g., 'depth' is mandatory for RB; 'groups' is mandatory for Simultaneous RB).
        execution_results: The output list of (ideal, noisy) tuples.
                           This function primarily extracts the 2nd element (index 1) for RB analysis.

    Returns:
        A list of dictionaries suitable for `analyze_rb_standard` or `analyze_rb_simultaneous`.

    Example Scenario:
    -----------------
    >>> # 1. Define Circuits with Metadata
    >>> # Crucial: 'depth' is required for curve fitting.
    >>> c1 = QuantumCircuit(qubits=[0]); c1.metadata = {"depth": 2, "sample_idx": 0}
    >>> c2 = QuantumCircuit(qubits=[0]); c2.metadata = {"depth": 4, "sample_idx": 0}
    >>> circuits_list = [c1, c2]
    >>>
    >>> # 2. Prepare Execution Results (Tuple Format)
    >>> # Format: List[Tuple[Ideal_Data, Experimental_Counts]]
    >>> # Note: We use `None` for ideal data here as RB fitting only needs the counts.
    >>> raw_results = [
    ...     (None, {"0": 1020, "1": 4}),   # Result for c1 (Depth 2)
    ...     (None, {"0": 980, "1": 44})    # Result for c2 (Depth 4)
    ... ]
    >>>
    >>> # 3. Stitch for Analyzer
    >>> structured_data = stitch_rb_results(circuits_list, raw_results)
    >>> # The output is now ready for 'analyze_rb_standard(structured_data)'
    """
    stitched_data = []
    # Zipping ensures we match the N-th circuit with the N-th result
    for circ, res_tuple in zip(circuits, execution_results):
        # res_tuple[1] is conventionally the noisy_counts in EGM engines
        # res_tuple[0] is ideal_probs (ignored here but kept in tuple for compatibility)
        stitched_item = {
            "data": res_tuple[1],
            "metadata": circ.metadata
        }
        stitched_data.append(stitched_item)
    return stitched_data


# ---------------------------------------------------------------------
# Core Decay Model
# ---------------------------------------------------------------------
def _rb_decay_function(m: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """Standard RB model: f(m) = A * p^m + B."""
    return A * (p ** m) + B


# ---------------------------------------------------------------------
# Flexible RB Fit Routine (Low-Level Math)
# ---------------------------------------------------------------------
def fit_rb_data(
        depths: Optional[List[int]] = None,
        means: Optional[List[float]] = None,
        stds: Optional[List[float]] = None,
        num_qubits: int = 1,
        survivals: Optional[Dict[int, List[float]]] = None,
        gate_counts: Optional[Dict[int, float]] = None,
) -> Dict[str, Any]:
    """
    Fit Randomized-Benchmarking decay curves. Returns raw dictionary.
    """
    # ------------------------------------------------------------------
    # Pre-process Input Data
    # ------------------------------------------------------------------
    if survivals is not None:
        depths_arr = np.array(sorted(survivals.keys()), dtype=float)
        means_arr = np.array([np.mean(survivals[d]) for d in depths_arr])
        stds_arr = np.array([
            np.std(survivals[d], ddof=1) / np.sqrt(max(len(survivals[d]), 1))
            for d in depths_arr
        ])
    else:
        depths_arr = np.array(depths or [], dtype=float)
        means_arr = np.array(means or [], dtype=float)
        stds_arr = np.array(stds or [1.0] * len(means_arr), dtype=float)

    if len(depths_arr) < 3:
        return _result_failure("Insufficient data points (<3) for RB fit.")

    d = 2 ** num_qubits
    gate_array = (
        np.array([gate_counts.get(int(m), np.nan) for m in depths_arr])
        if gate_counts else np.full_like(depths_arr, np.nan)
    )

    # ------------------------------------------------------------------
    # Initial Guesses & Result Container Initialization
    # ------------------------------------------------------------------
    init = [1 - 1 / d, _DEFAULT_P_GUESS, 1 / d]
    bounds = ([0, 0, 0], [1, 1.0, 1])

    results = {
        "fit_successful": False,
        "A": np.nan, "B": np.nan, "p": np.nan,
        "epc": np.nan, "r_squared": np.nan,
        "depths": depths_arr.tolist(),
        "means": means_arr.tolist(),
        "std_errors": stds_arr.tolist(),
        "gate_counts": gate_array.tolist(),
        "fit_x": [], "fit_y": [],
        "message": "Not fitted.",
    }

    # ------------------------------------------------------------------
    # Curve Fit Execution
    # ------------------------------------------------------------------
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OptimizeWarning)
        try:
            popt, pcov = curve_fit(
                _rb_decay_function,
                depths_arr,
                means_arr,
                p0=init,
                sigma=stds_arr,
                bounds=bounds,
                absolute_sigma=True,
                maxfev=_MAX_EVALS,
            )
            A, p, B = popt
            epc = ((d - 1) / d) * (1 - p)

            residuals = means_arr - _rb_decay_function(depths_arr, *popt)
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((means_arr - np.mean(means_arr)) ** 2)
            r_sq = 1 - ss_res / ss_tot if ss_tot > 1e-12 else np.nan

            fit_x = np.linspace(min(depths_arr), max(depths_arr), 200)
            fit_y = _rb_decay_function(fit_x, *popt)

            results.update({
                "fit_successful": True,
                "A": float(A),
                "B": float(B),
                "p": float(p),
                "epc": float(epc),
                "r_squared": float(r_sq),
                "fit_x": fit_x.tolist(),
                "fit_y": fit_y.tolist(),
                "message": "Fit successful.",
            })
            logging.info(
                f"[RB-FIT] Success: A={A:.3f}, p={p:.5f}, B={B:.3f}, "
                f"EPC={epc:.3e}, R²={r_sq:.4f}"
            )

        except Exception as exc:
            results["message"] = f"Fit failed: {exc!s}"
            logging.warning(results["message"])

    return results


# ---------------------------------------------------------------------
# Error per Gate Calculation
# ---------------------------------------------------------------------
def calculate_epg(p_std: float, p_interleaved: float, num_qubits: int) -> float:
    """Compute Error Per Gate (EPG) using standard and interleaved p."""
    d = 2 ** num_qubits
    if p_std <= 0:
        logging.warning("Invalid p_std <= 0; returning EPG = 1.0")
        return 1.0
    epg = ((d - 1) / d) * (1 - p_interleaved / (p_std + 1e-12))
    return float(epg)


# =============================================================================
# High-Level Analyzers (Integrated with Schemas)
# =============================================================================

def analyze_rb_standard(
        results: List[Dict[str, Any]]
) -> RBAnalysisResult:
    """
    Standard Analysis: Aggregates stitched data, fits RB curve, and returns Schema.

    Args:
        results: List of dicts, each containing:
                 - "data": Dict[str, int|float] (Counts or Probs)
                 - "metadata": Dict[str, Any] (Must contain "depth")

    Returns:
        RBAnalysisResult: Standardized schema object.
    """
    if not results:
        raise ValueError("Analysis received empty results list.")

    # 0. Infer Qubit Count from Data Keys
    first_item_data = results[0]["data"]
    if not first_item_data:
        raise ValueError("First result entry contains no data.")

    num_qubits = len(next(iter(first_item_data.keys())))
    ground_state = "0" * num_qubits

    # 1. Organize data by depth
    depths = sorted(list(set(item["metadata"]["depth"] for item in results)))
    depth_map = {d: [] for d in depths}

    # Process results
    for item in results:
        d = item["metadata"]["depth"]
        data_map = item["data"]

        # [Data Handling] Threshold Check for Robustness
        # If total > 1.1, it's Counts (e.g., 1024) -> Normalize.
        # If total <= 1.1, it's Probs -> Do NOT normalize (avoids truncation bug).
        total = sum(data_map.values())

        if total > 1.1:
            # Case: Counts
            p = data_map.get(ground_state, 0.0) / total
        else:
            # Case: Probabilities (Safe against sparse truncation)
            p = data_map.get(ground_state, 0.0)

        depth_map[d].append(p)

    # 2. Aggregate Data Points
    agg_depths = []
    agg_means = []
    agg_stds = []
    sequence_data_points = []

    for d in depths:
        probs = depth_map[d]
        if not probs:
            continue

        mean_val = np.mean(probs)
        std_err = np.std(probs, ddof=1) / np.sqrt(len(probs)) if len(probs) > 1 else 0.0

        agg_depths.append(d)
        agg_means.append(mean_val)
        agg_stds.append(std_err)

        sequence_data_points.append(RBSequenceDataPoint(
            sequence_length=d,
            survival_probability=float(mean_val),
            std_error=float(std_err)
        ))

    # 3. Perform Fitting
    fit_res_dict = fit_rb_data(
        depths=agg_depths,
        means=agg_means,
        stds=agg_stds,
        num_qubits=num_qubits
    )

    # 4. Construct Schemas
    fit_obj = FitResult(
        model_name="standard_rb_decay",
        params=[
            FitParameter(name="A", value=fit_res_dict.get("A", 0.0)),
            FitParameter(name="B", value=fit_res_dict.get("B", 0.0)),
            FitParameter(name="p", value=fit_res_dict.get("p", 0.0)),
        ],
    )

    qubits_meta = list(range(num_qubits))
    if "remapped_from" in results[0]["metadata"]:
        qubits_meta = results[0]["metadata"]["remapped_from"]

    result_obj = RBAnalysisResult(
        analyzer_version="Modular_v5.4",
        qubits=qubits_meta,
        plan_id=uuid4(),
        raw_data_ids=[uuid4()],
        tags=["standard_rb"],
        notes=f"EPC: {fit_res_dict.get('epc', -1):.2e}",
        success=fit_res_dict.get("fit_successful", False),
        fit=fit_obj,
        error_message=None if fit_res_dict.get("fit_successful") else "Fit failed",
        depths=agg_depths,
        means=agg_means,
        stds=agg_stds,
        sequence_data=sequence_data_points
    )

    return result_obj


def analyze_rb_simultaneous(
        results: List[Dict[str, Any]]
) -> Dict[Tuple[int, ...], RBAnalysisResult]:
    """
    Simultaneous Analysis: Marginalizes results for disjoint groups and fits independently.
    """
    if not results:
        raise ValueError("Analysis received empty results list.")

    # 0. Extract Configuration from Metadata
    first_meta = results[0]["metadata"]
    if "groups" not in first_meta:
        raise ValueError("Simultaneous analysis requires 'groups' in metadata.")

    qubit_groups = [tuple(g) for g in first_meta["groups"]]

    first_data = results[0]["data"]
    total_qubits_len = len(next(iter(first_data.keys())))
    system_qubits = list(range(total_qubits_len))

    # 1. Prepare Container
    all_depths = sorted(list(set(item["metadata"]["depth"] for item in results)))
    group_survivals = {g: {d: [] for d in all_depths} for g in qubit_groups}

    # 2. Marginalize
    for item in results:
        d = item["metadata"]["depth"]
        data_map = item["data"]

        for g in qubit_groups:
            # Calculate marginal probability for this group
            prob = _rb_local_survival_from_counts(
                data_map,
                all_qubits=system_qubits,
                target_qubits=g
            )
            group_survivals[g][d].append(prob)

    # 3. Fit and Build Schema per Group
    final_results = {}

    for g_tuple, survivals_map in group_survivals.items():
        num_q = len(g_tuple)

        agg_depths, agg_means, agg_stds, sequence_data = [], [], [], []

        for d in all_depths:
            probs = survivals_map[d]
            if not probs: continue

            mean_val = np.mean(probs)
            std_err = np.std(probs, ddof=1) / np.sqrt(len(probs)) if len(probs) > 1 else 0.0

            agg_depths.append(d)
            agg_means.append(mean_val)
            agg_stds.append(std_err)
            sequence_data.append(RBSequenceDataPoint(
                sequence_length=d, survival_probability=float(mean_val), std_error=float(std_err)
            ))

        # Fit
        fit_res_dict = fit_rb_data(
            depths=agg_depths, means=agg_means, stds=agg_stds, num_qubits=num_q
        )

        # Build Schema
        fit_obj = FitResult(
            model_name="simultaneous_rb_decay",
            params=[
                FitParameter(name="A", value=fit_res_dict.get("A", 0.0)),
                FitParameter(name="B", value=fit_res_dict.get("B", 0.0)),
                FitParameter(name="p", value=fit_res_dict.get("p", 0.0)),
            ]
        )

        schema_obj = RBAnalysisResult(
            analyzer_version="Modular_v5.4",
            qubits=list(g_tuple),
            plan_id=uuid4(),
            raw_data_ids=[uuid4()],
            tags=["simultaneous_rb"],
            notes=f"EPC: {fit_res_dict.get('epc', -1):.2e}",
            success=fit_res_dict.get("fit_successful", False),
            fit=fit_obj,
            error_message=None if fit_res_dict.get("fit_successful") else "Fit failed",
            depths=agg_depths,
            means=agg_means,
            stds=agg_stds,
            sequence_data=sequence_data
        )

        final_results[g_tuple] = schema_obj

    return final_results


# ---------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------

def _result_failure(msg: str) -> Dict[str, Any]:
    """Helper to return a standardized failure dict."""
    logging.warning(f"[RB-FIT] {msg}")
    return {
        "fit_successful": False,
        "A": np.nan, "B": np.nan, "p": np.nan,
        "epc": np.nan, "r_squared": np.nan,
        "depths": [], "means": [], "std_errors": [],
        "gate_counts": [], "fit_x": [], "fit_y": [],
        "message": msg,
    }


def _rb_local_survival_from_counts(
        data_map: Dict[str, float],
        all_qubits: List[int],
        target_qubits: Sequence[int]
) -> float:
    """
    Internal helper to calculate survival probability for a subset of qubits.
    Robustly handles both Counts and Probabilities using threshold logic.
    """
    indices = [all_qubits.index(q) for q in target_qubits]
    target_len = len(target_qubits)
    ground_pattern = "0" * target_len

    total_weight = 0.0
    success_weight = 0.0

    for bitstring, val in data_map.items():
        try:
            # Extract substring for target qubits
            extracted = "".join([bitstring[i] for i in indices])
            total_weight += val

            if extracted == ground_pattern:
                success_weight += val
        except IndexError:
            # Handle potential bitstring length mismatch
            pass

    # [Fixed Logic] Threshold check to avoid truncating error info
    if total_weight > 1.1:
        # It's counts, normalize it.
        return success_weight / total_weight
    else:
        # It's probabilities (likely truncated), do not normalize.
        return success_weight