# errorgnomark/analysis/benchmarking/xeb_analysis.py
from typing import Dict
import numpy as np

def _counts_to_probs_vector(counts: Dict[str, int], num_qubits: int) -> np.ndarray:
    """
    Converts a dictionary of measurement counts into a normalized probability vector.

    The vector is ordered by the integer representation of the bitstring keys.
    Example: For 2 qubits, the order is '00', '01', '10', '11'.

    Args:
        counts: A dictionary mapping bitstring outcomes to their counts.
                Example: {'0': 500, '1': 500}
        num_qubits: The number of qubits in the circuit.

    Returns:
        A numpy array representing the probability distribution.
    """
    total_shots = sum(counts.values())
    if total_shots == 0:
        return np.zeros(2**num_qubits)

    dimension = 2**num_qubits
    probs_vector = np.zeros(dimension)

    for bitstring, count in counts.items():
        # Convert bitstring '010' to integer index 2
        index = int(bitstring, 2)
        probs_vector[index] = count / total_shots
    
    return probs_vector

def analyze_xeb_fidelity(
    ideal_counts: Dict[str, int],
    noisy_counts: Dict[str, int]
) -> float:
    """
    Analyzes and calculates the XEB fidelity from ideal and noisy count dictionaries.

    This function first converts the count dictionaries into probability distributions
    and then computes the linear cross-entropy fidelity.

    Args:
        ideal_counts: The count dictionary from a noiseless simulation.
                      Example: {'0': 0, '1': 1000}
        noisy_counts: The count dictionary from a noisy simulation or real experiment.
                      Example: {'0': 50, '1': 950}

    Returns:
        The calculated Linear Cross-Entropy fidelity.
    """
    if not ideal_counts or not noisy_counts:
        raise ValueError("Input count dictionaries cannot be empty.")

    # Determine the number of qubits from the length of a key in the dictionary.
    # We assume all keys in a dictionary have the same length.
    num_qubits = len(next(iter(ideal_counts.keys())))
    
    # Validate that both dictionaries are for the same number of qubits
    noisy_num_qubits = len(next(iter(noisy_counts.keys())))
    if num_qubits != noisy_num_qubits:
        raise ValueError(
            f"Mismatch in number of qubits between ideal ({num_qubits}) "
            f"and noisy ({noisy_num_qubits}) counts."
        )

    # Convert count dictionaries to probability vectors
    ideal_probs = _counts_to_probs_vector(ideal_counts, num_qubits)
    noisy_probs = _counts_to_probs_vector(noisy_counts, num_qubits)

    # Calculate XEB fidelity using the same underlying formula
    dimension = 2**num_qubits
    dot_product = np.dot(ideal_probs, noisy_probs)
    
    # Fidelity formula: F = D * <p_ideal, p_noisy> - 1
    fidelity = dimension * dot_product - 1
    
    return fidelity

# --- Example Usage ---
if __name__ == '__main__':
    # Let's test with a simple single-qubit example.
    # Suppose the ideal circuit should always produce the |1> state.
    # With 1000 shots, the ideal result is deterministic.
    ideal_example_counts = {'0': 0, '1': 1000}

    # In a noisy run, some |1> states decay to |0>.
    # Let's say we get 5% error.
    noisy_example_counts = {'0': 50, '1': 950}

    print(f"Ideal Counts: {ideal_example_counts}")
    print(f"Noisy Counts: {noisy_example_counts}")

    # Calculate the fidelity
    calculated_fidelity = analyze_xeb_fidelity(ideal_example_counts, noisy_example_counts)
    
    print(f"\nCalculated XEB Fidelity: {calculated_fidelity:.4f}")

    # --- Manual Verification ---
    # num_qubits = 1, dimension = 2
    # ideal_probs = [0.0, 1.0]
    # noisy_probs = [0.05, 0.95]
    # dot_product = (0.0 * 0.05) + (1.0 * 0.95) = 0.95
    # expected_fidelity = 2 * 0.95 - 1 = 1.9 - 1 = 0.9
    print(f"Expected Fidelity: 0.9000")