# errorgnomark/analysis/benchmarking/csb.py 

import numpy as np
import scipy.linalg
from typing import Dict, List, Tuple, Any

try:
    from errorgnomark.circuits.circuit import Gate
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    from errorgnomark.circuits.circuit import Gate


def _matrix_pencil(data: np.ndarray, L: int, N_poles: int, cutoff: float = 1e-10) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # (This function is correct, no changes needed)
    N = len(data)
    if L < 1 or L >= N:
        L = max(1, int(N / 2.5))

    # Construct the Hankel matrix
    hankel_matrix = scipy.linalg.hankel(data[:N-L], data[N-L-1:])
    
    try:
        U, S_vals, Vh = scipy.linalg.svd(hankel_matrix, full_matrices=False)
    except np.linalg.LinAlgError as e:
        raise RuntimeError(f"SVD on Hankel matrix failed: {e}")

    valid_indices = np.where(S_vals > cutoff * S_vals[0])[0]
    if len(valid_indices) == 0:
        return np.array([]), np.array([]), S_vals

    M = min(N_poles, len(valid_indices))
    if M == 0:
         return np.array([]), np.array([]), S_vals

    # Truncate SVD matrices
    U_prime = U[:, :M]
    Vh_prime = Vh[:M, :]

    # Create shifted matrices
    U_down = U_prime[:-1, :]
    U_up = U_prime[1:, :]
    
    # Solve for poles using the shift-invariance property
    Z_matrix = np.linalg.pinv(U_down) @ U_up
    poles, _ = scipy.linalg.eig(Z_matrix)

    # Solve for amplitudes using least squares
    Z_vandermonde = np.array([[p**k for p in poles] for k in range(N)])
    amplitudes, _, _, _ = scipy.linalg.lstsq(Z_vandermonde, data)
    
    return poles, amplitudes, S_vals

def analyze_csb_data_1q(
    results_by_mode: Dict[str, List[Dict[str, int]]],
    gate_to_benchmark: Gate,
    reps: int,
    shots: int
) -> Dict[str, Any]:
    # This function was working correctly and remains unchanged.
    probs_by_mode = {}
    for mode, counts_list in results_by_mode.items():
        # For 1Q, we expect '0' or '1'. We track the probability of '0'.
        probs_by_mode[mode] = [
            counts.get('0', 0) / shots if shots > 0 else 0.0 for counts in counts_list
        ]

    data_x = np.array(probs_by_mode.get('x', []))
    data_y = np.array(probs_by_mode.get('y', [])) # Assuming y-basis prep gives <Y>
    
    if len(data_x) == 0 or len(data_y) == 0 or len(data_x) != len(data_y):
        return {"error": "Insufficient or mismatched data in X/Y modes for 1Q analysis."}
    
    complex_signal = (data_x - 0.5) - 1j * (data_y - 0.5)

    try:
        poles, _, _ = _matrix_pencil(complex_signal, L=int(len(complex_signal)/3), N_poles=4)
    except Exception as e:
        return {"error": f"Matrix Pencil failed: {e}"}

    if len(poles) < 1:
        return {"error": "Matrix Pencil failed to find any poles."}

    gate_name = gate_to_benchmark.name.lower()
    if gate_name in ['x', 'y', 'rx', 'ry']: target_phase = np.pi
    elif gate_name in ['z', 'rz', 's', 't', 'sdg', 'tdg']:
        if gate_to_benchmark.params: target_phase = gate_to_benchmark.params[0]
        else:
            if gate_name == 'z': target_phase = np.pi
            elif gate_name == 's': target_phase = np.pi / 2
            elif gate_name == 't': target_phase = np.pi / 4
            elif gate_name == 'sdg': target_phase = -np.pi / 2
            elif gate_name == 'tdg': target_phase = -np.pi / 4
            else: target_phase = 0
    else: target_phase = 0
    
    amp, phase = np.abs(poles), np.angle(poles)
    signal_index = np.argmax(amp)
    target_phase_p = (target_phase * reps)
    
    raw_diff = phase[signal_index] - target_phase_p
    angle_diff_wrapped = (raw_diff + np.pi) % (2 * np.pi) - np.pi
    angle_error = angle_diff_wrapped / reps
    
    other_indices = [i for i in range(len(poles)) if i != signal_index]
    other_amps = sorted([amp[i] for i in other_indices], reverse=True)
    
    p_coh = amp[signal_index]**(1/reps)
    p_incoh1 = other_amps[0]**(1/reps) if len(other_amps) > 0 else 0
    p_incoh2 = other_amps[1]**(1/reps) if len(other_amps) > 1 else 0

    process_infidelity = 1 - (0.5 * p_coh * np.cos(angle_error * reps) + 0.25 * (p_incoh1 + p_incoh2))
    stochastic_infidelity = 1 - np.sqrt((2 * p_coh**2 + p_incoh1**2 + p_incoh2**2) / 4)

    return {
        "process_infidelity": max(0.0, min(1.0, process_infidelity)),
        "stochastic_infidelity": max(0.0, min(1.0, stochastic_infidelity)),
        "angle_error": angle_error
    }


def analyze_csb_data_2q(
    results_by_mode: Dict[str, List[Dict[str, int]]],
    gate_to_benchmark: Gate,
    reps: int,
    shots: int
) -> Dict[str, Any]:
    """
    Analyzes 2-qubit CSB data by processing multiple eigenstate-pair modes.
    This logic is adapted from the user-provided Csb_fsim reference code.
    """
    num_qubits = 2
    target_bitstring = '0' * num_qubits # We measure the survival probability P(|ψ_prep>)

    if not results_by_mode or not any(results_by_mode.values()):
        return {"error": "No data provided for 2Q analysis."}

    # Step 1: Convert counts to survival probabilities for each mode
    probs_by_mode = {}
    for mode, counts_list in results_by_mode.items():
        # The survival probability is the probability of measuring the all-zeros bitstring '00'
        # because the inverse state prep maps the initial state back to |00>.
        probs_by_mode[mode] = np.array([
            counts.get(target_bitstring, 0) / shots if shots > 0 else 0.0 for counts in counts_list
        ])

    # Step 2: Define target phases for each mode for a CNOT-like gate
    # This maps eigenstate pairs to their expected phase difference (0 or pi).
    # This is a simplified mapping assuming a Bell basis.
    target_phases = {
        '01': np.pi, '02': 0, '03': 0, # Superpositions with |Φ+>
        '12': np.pi, '13': np.pi,      # Superpositions with |Φ->
        '23': 0                       # Superposition of |Ψ+> and |Ψ->
    }

    ns_poles = []  # Poles from Non-Trivial Subspace (phase != 0)
    ts_poles = []  # Poles from Trivial Subspace (phase == 0)
    angle_errors = []

    # Step 3: Run Matrix Pencil on each mode and process the poles
    for mode, data in probs_by_mode.items():
        if len(data) < 4: continue # Not enough data for this mode

        target_phase = target_phases.get(mode, 0)
        
        try:
            poles, _, _ = _matrix_pencil(data, L=int(len(data)/2.5), N_poles=4)
        except Exception as e:
            return {"error": f"Matrix Pencil failed for mode {mode}: {e}"}

        if len(poles) == 0: continue

        # Process poles similar to the reference code's 'mp_est'
        amps, phases = np.abs(poles), np.angle(poles)
        
        target_phase_p = (target_phase * reps) % (2 * np.pi)
        
        # Find the pole corresponding to the signal
        phase_diffs = np.abs(phases - target_phase_p)
        phase_diffs = np.minimum(phase_diffs, 2 * np.pi - phase_diffs) # Handle wraparound
        signal_index = np.argmin(phase_diffs)
        
        # Normalize pole magnitude by number of repetitions
        processed_pole = amps[signal_index]**(1/reps)

        if np.abs(target_phase) > 1e-6: # Non-trivial subspace
            ns_poles.append(processed_pole)
            raw_diff = phases[signal_index] - target_phase_p
            angle_error = (raw_diff + np.pi) % (2 * np.pi) - np.pi
            angle_errors.append(angle_error / reps)
        else: # Trivial subspace
            ts_poles.append(processed_pole)

    if not ns_poles and not ts_poles:
        return {"error": "Failed to extract any valid poles from the data."}

    # Step 4: Calculate final metrics by averaging, as in reference 'result_mp'
    dim = 4
    # For CNOT/CZ, the eigenspaces are typically split into two 2D spaces for the
    # trivial (+1) and non-trivial (-1) eigenvalues.
    dim_ts = 8 # Dimension of trivial subspace in Pauli Transfer Matrix
    dim_ns = 8 # Dimension of non-trivial subspace
    
    f_ns_mean = np.mean(ns_poles) if ns_poles else 1.0
    f_ts_mean = np.mean(ts_poles) if ts_poles else 1.0
    
    # Weighted average for process fidelity
    process_fidelity = (dim_ns * f_ns_mean + dim_ts * f_ts_mean) / (dim**2)

    # Weighted average for stochastic fidelity
    u_ns_mean = np.mean(np.square(ns_poles)) if ns_poles else 1.0
    u_ts_mean = np.mean(np.square(ts_poles)) if ts_poles else 1.0
    stochastic_fidelity_squared = (dim_ns * u_ns_mean + dim_ts * u_ts_mean) / (dim**2)

    return {
        "process_infidelity": 1 - process_fidelity,
        "stochastic_infidelity": 1 - np.sqrt(stochastic_fidelity_squared),
        "theta_error": np.mean(angle_errors) if angle_errors else 0.0,
        "phi_error": 0.0  # This model simplifies to a single angle error
    }