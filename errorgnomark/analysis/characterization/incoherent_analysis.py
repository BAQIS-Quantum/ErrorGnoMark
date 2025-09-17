# File Path: errorgnomark/analysis/characterization/incoherent_analysis.py
# MODIFIED to fix calculation formulas and handle units correctly.

from typing import List, Dict, Any, Tuple
import numpy as np
from scipy.optimize import curve_fit

# --- T1 Analysis ---

def _t1_decay_model(t, T1, A, B):
    """Exponential decay model for T1."""
    return A * np.exp(-t / T1) + B

def analyze_t1(results: List[Dict[str, int]], delays_us: np.ndarray, qubits: List[int], shots: int) -> Dict[str, Any]:
    """Analyzes T1 experiment results, returning a dictionary."""
    # --- FIX 2: Convert delay units from microseconds to seconds for fitting ---
    delays_s = delays_us * 1e-6
    
    y_data = np.array([res.get('1', 0) / shots for res in results])
    x_data = delays_s

    # T1 is in seconds, so the initial guess should be in seconds.
    initial_guess = [np.mean(delays_s), 1.0, 0.0]
    popt, _ = curve_fit(_t1_decay_model, x_data, y_data, p0=initial_guess)
    
    t1_val_s = popt[0]

    return {
        'qubit': qubits[0],
        't1': t1_val_s * 1e6, # Convert back to microseconds for reporting
        'fit_parameters': {'A': popt[1], 'B': popt[2]}
    }

# --- T2 Echo Analysis ---

def analyze_t2_echo(results: List[Dict[str, int]], delays_us: np.ndarray, qubits: List[int], shots: int) -> Dict[str, Any]:
    """Analyzes T2 Echo experiment results, returning a dictionary."""
    # --- FIX 2: Convert delay units from microseconds to seconds for fitting ---
    delays_s = delays_us * 1e-6
    
    y_data = np.array([res.get('0', 0) / shots for res in results])
    x_data = delays_s

    def echo_model(t, T2, A, B):
        return A * np.exp(-t / T2) + B

    initial_guess = [np.mean(delays_s), 0.5, 0.5]
    popt, _ = curve_fit(echo_model, x_data, y_data, p0=initial_guess, bounds=([0, 0, 0], [np.inf, 1, 1]))
    
    t2_val_s = popt[0]

    return {
        'qubit': qubits[0],
        't2': t2_val_s * 1e6, # Convert back to microseconds for reporting
        'fit_parameters': {'A': popt[1], 'B': popt[2]}
    }

# --- Pauli Twirling Analysis ---

def analyze_pauli_twirling(results: List[Tuple[Dict[str, Any], Dict[str, int]]], qubits: List[int], gate_name: str) -> Dict[str, Any]:
    """Analyzes the results of a Pauli Twirling experiment."""
    total_shots = sum(results[0][1].values())
    
    survival_probs = {}
    for metadata, counts in results:
        p_i = metadata['p_i']
        expected_outcome = metadata['expected_outcome']
        prob = counts.get(expected_outcome, 0) / total_shots
        survival_probs[p_i] = prob
        
    # --- FIX 1: Use the correct formula for depolarizing parameter and fidelity ---
    # Calculate the average survival probability
    avg_survival_prob = (survival_probs['I'] + survival_probs['X'] + survival_probs['Y'] + survival_probs['Z']) / 4.0
    
    # For a single qubit (d=2), the depolarizing parameter p is given by:
    # avg_survival_prob = (p + 1) / 2  =>  p = 2 * avg_survival_prob - 1
    p = 2 * avg_survival_prob - 1
    
    # Fidelity F = (d*p + 1)/(d+1) for d=2
    d = 2
    fidelity = (d * p + 1) / (d + 1)
    
    return {
        'qubit': qubits[0],
        'gate_name': gate_name,
        'fidelity': fidelity,
        'depolarizing_parameter': p
    }