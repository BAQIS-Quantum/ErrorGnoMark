import sys

from errorgnomark.cirpulse_generator.qubit_selector import qubit_selection, chip
import random
from typing import List, Dict

def generate_fake_data_rbq1(
    length_max: int = 10, 
    ncr: int = 10, 
    shots: int = 4096
) -> List[List[List[Dict[str, int]]]]:
    """
    Generates fake data for 1-qubit benchmarking, returning a three-tiered structure:
    - Outer Layer: Qubit index list
    - Middle Layer: Circuit length list
    - Inner Layer: `ncr` measurement count dictionaries

    Parameters:
        length_max (int): Maximum circuit length.
        ncr (int): Number of circuits per length.
        shots (int): Number of shots per circuit.

    Returns:
        List[List[List[Dict[str, int]]]]: Three-tier nested fake data structure.
    """
    # Define selection options
    selection_options = {
        'max_qubits_per_row': 4,    
        'min_qubit_index': 3,       
        'max_qubit_index': 50       
    }

    # Instantiate qubit_selection with the desired constraints
    selector = qubit_selection(
        chip=chip(rows=13, columns=13),  
        qubit_index_max=50,
        qubit_number=6,
        option=selection_options
    )

    # Perform qubit selection
    selection = selector.quselected()
    qubit_index_list = selection["qubit_index_list"]

    all_results = []
    for qubit in qubit_index_list:
        qubit_results = []
        for length in range(1, length_max + 1):
            length_results = []
            for _ in range(ncr):
                # Generate fake measurement counts with slight random fluctuations
                base_zero = 0.9
                zero_prob = base_zero + random.uniform(-0.001, 0.05)  # ±5%
                one_prob = 1.0 - zero_prob

                count_zero = max(int(shots * zero_prob), 0)
                count_one = shots - count_zero

                fake_result = {
                    '0': count_zero,
                    '1': count_one
                }
                length_results.append(fake_result)
            qubit_results.append(length_results)
        all_results.append(qubit_results)

    return all_results


def generate_fake_data_rbq2(
    length_max: int = 10, 
    ncr: int = 10, 
    shots: int = 1024
) -> List[List[List[Dict[str, int]]]]:
    """
    Generates fake data for 2-qubit benchmarking, returning a three-tiered structure:
    - Outer Layer: Qubit pair list
    - Middle Layer: Circuit length list
    - Inner Layer: `ncr` measurement count dictionaries

    Parameters:
        length_max (int): Maximum circuit length.
        ncr (int): Number of circuits per length.
        shots (int): Number of shots per circuit.

    Returns:
        List[List[List[Dict[str, int]]]]: Three-tier nested fake data structure.
    """
    # Define selection options
    selection_options = {
        'max_qubits_per_row': 3,    
        'min_qubit_index': 3,       
        'max_qubit_index': 29     
    }

    # Instantiate qubit_selection with the desired constraints
    selector = qubit_selection(
        chip=chip(rows=13, columns=13),  
        qubit_index_max=29,
        qubit_number=12,
        option=selection_options
    )

    # Perform qubit selection
    selection = selector.quselected()
    qubit_connectivity = selection["qubit_connectivity"]
    # print ('qubit_connectivity ',qubit_connectivity )

    all_results = []
    for qubit_pair in qubit_connectivity:
        qubit_pair_results = []
        for length in range(1, length_max + 1):
            length_results = []
            for _ in range(ncr):
                # Generate fake measurement counts with slight random fluctuations
                base_00 = 0.8
                base_01 = 0.15
                base_10 = 0.04
                base_11 = 0.01

                # Introduce slight random variations
                variation_00 = random.uniform(-0.02, 0.02)  # ±2% for |00>
                prob_00 = base_00 + variation_00
                prob_01 = base_01 + random.uniform(-0.01, 0.01)
                prob_10 = base_10 + random.uniform(-0.005, 0.005)  # Allow both increases and decreases
                prob_11 = 1.0 - (prob_00 + prob_01 + prob_10)  # Ensure probabilities sum to 1

                # Handle potential negative probabilities
                prob_00 = max(prob_00, 0)
                prob_01 = max(prob_01, 0)
                prob_10 = max(prob_10, 0)
                prob_11 = max(prob_11, 0)

                # Re-normalize probabilities to ensure they sum to 1
                total_prob = prob_00 + prob_01 + prob_10 + prob_11
                if total_prob == 0:
                    prob_00, prob_01, prob_10, prob_11 = 0.25, 0.25, 0.25, 0.25
                else:
                    prob_00 /= total_prob
                    prob_01 /= total_prob
                    prob_10 /= total_prob
                    prob_11 /= total_prob

                # Calculate measurement counts
                count_00 = max(int(shots * prob_00), 0)
                count_01 = max(int(shots * prob_01), 0)
                count_10 = max(int(shots * prob_10), 0)
                count_11 = shots - (count_00 + count_01 + count_10)  # Ensure total counts equal shots

                fake_result = {
                    '00': count_00,
                    '01': count_01,
                    '10': count_10,
                    '11': count_11
                }
                length_results.append(fake_result)
            qubit_pair_results.append(length_results)
        all_results.append(qubit_pair_results)

    return all_results




# # Example usage with dynamic qubit indices and connectivity
# if __name__ == '__main__':
#     # Generate fake data for 1-qubit and 2-qubit benchmarks
#     fake_data_q1 = generate_fake_data_rbq1()
#     fake_data_q2 = generate_fake_data_rbq2()

# print ('fake_data_q1',len(fake_data_q1))
# print ('fake_data_q2',len(fake_data_q2))