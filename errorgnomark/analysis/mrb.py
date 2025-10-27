# File Path: errorgnomark/analysis/mrb.py
# [NEW FILE - This file should be created in the 'analysis' directory]

"""
Module for analyzing Mirrored Randomized Benchmarking (MRB) experiments.

This module provides functions to fit the exponential decay of sequence fidelity
and to compute the polarization from measurement outcomes, which are key steps in
determining the Error Per Clifford (EPC).
"""

import numpy as np
from typing import Dict, List, Tuple, TypedDict
from scipy.optimize import curve_fit

# --- Type Definitions for Clarity ---

class MRBFitResult(TypedDict):
    """
    A dictionary defining the structure of the return value from fit_mrb_decay.
    """
    fit_successful: bool
    A: float
    p: float
    B: float
    epc: float
    epc_err: float
    params: Tuple[float, float, float]
    param_errors: Tuple[float, float, float]

# --- Core Functions ---

def _mrb_decay_func(m: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """
    Defines the exponential decay model for randomized benchmarking.

    The model is F(m) = A * p^m + B, where:
      - m: The sequence depth (number of Cliffords).
      - A: Amplitude of the decay.
      - p: The depolarization parameter related to the fidelity of a single Clifford.
      - B: An offset, typically related to state preparation and measurement (SPAM) errors.

    Args:
        m: An array of sequence depths.
        A: The amplitude parameter.
        p: The decay parameter.
        B: The offset parameter.

    Returns:
        An array of the calculated survival probabilities based on the model.
    """
    return A * (p**m) + B

def fit_mrb_decay(survival_data: Dict[int, List[float]], num_qubits: int) -> MRBFitResult:
    """
    Fits survival probability data to the MRB exponential decay model.

    This function takes a dictionary of survival probabilities at different sequence
    depths, calculates the mean and standard error, and performs a weighted
    least-squares fit to the function F(m) = A * p^m + B. From the fit, it
    calculates the Error Per Clifford (EPC).

    Args:
        survival_data: A dictionary mapping sequence depth (int) to a list of
                       survival probabilities (float) for that depth.
        num_qubits: The number of qubits in the benchmarking experiment.

    Returns:
        A MRBFitResult dictionary containing the fit status, parameters (A, p, B),
        their errors, and the calculated EPC and its error. If the fit fails,
        parameter values will be NaN.
    """
    if not survival_data:
        return _create_failure_result()

    depths = np.array(sorted(survival_data.keys()))
    mean_survivals = np.array([np.mean(survival_data[d]) for d in depths])
    
    # Calculate the standard error of the mean (SEM) for weighting the fit.
    # If a depth has only one data point, its error is 0, giving it high weight.
    std_errors = np.array([
        np.std(survival_data[d], ddof=1) / np.sqrt(len(survival_data[d]))
        if len(survival_data[d]) > 1 else 0.0
        for d in depths
    ])

    # Heuristic initial guess for parameters [A, p, B]
    p0 = [
        mean_survivals[0] - mean_survivals[-1],  # Initial guess for A
        0.99,                                   # Initial guess for p
        mean_survivals[-1]                      # Initial guess for B
    ]

    try:
        popt, pcov = curve_fit(
            _mrb_decay_func,
            depths,
            mean_survivals,
            p0=p0,
            sigma=std_errors,
            absolute_sigma=True,  # `sigma` gives the true standard deviation.
            maxfev=10000,
            bounds=([-np.inf, 0, -np.inf], [np.inf, 1, np.inf]) # p must be <= 1
        )
        fit_successful = True
        A, p, B = popt
        param_errors = np.sqrt(np.diag(pcov))
        
        # Calculate Error per Clifford (EPC) from the decay parameter 'p'.
        # EPC = (d-1)/d * (1-p), where d = 2^n is the Hilbert space dimension.
        dimension = 2**num_qubits
        epc = (dimension - 1) * (1 - p) / dimension
        # Propagate the error from 'p' to 'epc'.
        epc_err = (dimension - 1) * param_errors[1] / dimension

        return {
            "fit_successful": fit_successful,
            "A": A, "p": p, "B": B,
            "epc": epc, "epc_err": epc_err,
            "params": tuple(popt),
            "param_errors": tuple(param_errors)
        }

    except (RuntimeError, ValueError):
        # RuntimeError: Optimal parameters not found.
        # ValueError: Can be raised by pcov calculation if fit is poor.
        return _create_failure_result()

def compute_polarization(counts: Dict[str, int], num_qubits: int) -> float:
    """
    Computes the effective polarization from measurement counts.

    Polarization is a measure of how much the final state distribution is
    concentrated on the target '00...0' state. It is calculated by summing
    the probabilities of measuring each Hamming distance, weighted by (-1)^k.

    Args:
        counts: A dictionary mapping a measured bitstring (str) to its count (int).
        num_qubits: The number of qubits.

    Returns:
        The computed polarization, a float value clamped between 0.0 and 1.0.
    """
    target_bitstring = '0' * num_qubits
    
    # Initialize a list to store counts for each Hamming distance k.
    # h_k[k] = number of shots with Hamming distance k from the target.
    h_k = [0] * (num_qubits + 1)
    
    for bitstring, count in counts.items():
        # Basic validation for robustness.
        if len(bitstring) != num_qubits:
            continue
        
        distance = sum(b1 != b2 for b1, b2 in zip(bitstring, target_bitstring))
        h_k[distance] += count
        
    total_counts = sum(h_k)
    if total_counts == 0:
        return 0.0
    
    # p_k[k] is the probability of measuring a state with Hamming distance k.
    p_k = [hk / total_counts for hk in h_k]
    
    # The polarization is the expectation value of the parity operator.
    # S = sum_{k=0 to n} (-1)^k * p_k
    s_val = sum(((-1) ** k) * p_k[k] for k in range(num_qubits + 1))
    
    # Clamp the result between 0 and 1, as physical polarization cannot
    # exceed these bounds. Small statistical fluctuations might cause this.
    return max(0.0, min(s_val, 1.0))

def _create_failure_result() -> MRBFitResult:
    """Helper function to generate a dictionary for a failed fit."""
    nan_tuple = (np.nan, np.nan, np.nan)
    return {
        "fit_successful": False,
        "A": np.nan, "p": np.nan, "B": np.nan,
        "epc": np.nan, "epc_err": np.nan,
        "params": nan_tuple,
        "param_errors": nan_tuple
    }