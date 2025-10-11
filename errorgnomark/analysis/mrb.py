# File Path: errorgnomark/analysis/mrb.py
# [NEW FILE - This file should be created in the 'analysis' directory]

import numpy as np
from typing import Dict, List
from scipy.optimize import curve_fit

def _mrb_decay_func(m: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """Defines the exponential decay model: F(m) = A * p^m + B"""
    return A * (p**m) + B

def fit_mrb_decay(survival_data: Dict[int, List[float]], num_qubits: int) -> Dict:
    """
    Fits the survival probability data to the MRB decay model.
    Returns a dictionary with fit parameters and results.
    """
    depths = np.array(sorted(survival_data.keys()))
    mean_survivals = np.array([np.mean(survival_data[d]) for d in depths])
    # Ensure standard error of the mean is used, not just standard deviation
    std_survivals = np.array([np.std(survival_data[d]) / np.sqrt(len(survival_data[d])) if len(survival_data[d]) > 1 else 0 for d in depths])

    # Initial guess for parameters [A, p, B]
    p0 = [mean_survivals[0] - mean_survivals[-1], 0.99, mean_survivals[-1]]

    try:
        params, params_covariance = curve_fit(
            _mrb_decay_func,
            depths,
            mean_survivals,
            p0=p0,
            sigma=std_survivals,
            absolute_sigma=True, # Important for correct error estimation
            maxfev=10000
        )
        fit_successful = True
        A, p, B = params
        param_errors = np.sqrt(np.diag(params_covariance))
        d = 2**num_qubits
        
        # Error per Clifford (EPC)
        epc = (d - 1) * (1 - p) / d
        epc_err = (d - 1) * param_errors[1] / d

    except RuntimeError:
        fit_successful = False
        A, p, B, epc, epc_err = (np.nan, np.nan, np.nan, np.nan, np.nan)
        params = (np.nan, np.nan, np.nan)
        param_errors = (np.nan, np.nan, np.nan)

    return {
        "fit_successful": fit_successful,
        "A": A, "p": p, "B": B,
        "epc": epc, "epc_err": epc_err,
        "params": params, "param_errors": param_errors
    }

def compute_polarization(counts: Dict[str, int], num_qubits: int) -> float:
    """
    Computes the effective polarization S_k from measurement counts.
    Corresponds to the old `_compute_S` method.
    """
    target_bitstring = '0' * num_qubits
    h_k = [0] * (num_qubits + 1)
    for bitstring, count in counts.items():
        if len(bitstring) != num_qubits: continue
        distance = sum(1 for a, b in zip(bitstring, target_bitstring) if a != b)
        if 0 <= distance <= num_qubits: h_k[distance] += count
        
    total_counts = sum(h_k)
    if total_counts == 0: return 0.0
    
    p_k = [hk / total_counts for hk in h_k]
    s_val = sum(((-1) ** k) * p_k[k] for k in range(num_qubits + 1))
    
    return max(0.0, min(s_val, 1.0))