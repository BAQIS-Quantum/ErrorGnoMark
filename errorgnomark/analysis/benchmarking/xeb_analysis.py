# errorgnomark/analysis/benchmarking/xeb_analysis.py
from typing import Dict, Any
import numpy as np

def analyze_xeb_fidelity(result: Dict[str, Any], num_qubits: int) -> float:
    """
    Analyzes and calculates the XEB fidelity from the raw data of a single run.

    Args:
        result: The single-run result dictionary returned by the Runner.
                Expected format: {'ideal_probs': ndarray, 'noisy_probs': ndarray}
        num_qubits: The number of qubits in the circuit.

    Returns:
        The calculated Linear Cross-Entropy fidelity.
    """
    ideal_probs = result['ideal_probs']
    noisy_probs = result['noisy_probs']
    
    if ideal_probs is None or noisy_probs is None:
        raise ValueError("Input dictionary is missing 'ideal_probs' or 'noisy_probs'.")

    dimension = 2**num_qubits
    dot_product = np.dot(ideal_probs, noisy_probs)
    
    fidelity = dimension * dot_product - 1
    return fidelity