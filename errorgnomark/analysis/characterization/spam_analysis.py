# errorgnomark/analysis/characterization/spam_analysis.py

from typing import List, Dict, Any, Union, Tuple

def analyze_spam(
    results: List[Tuple[Dict[str, int], Dict[str, Any]]], 
    qubits: List[int]
) -> Dict[str, Union[float, str]]:
    """
    Analyzes the results from a SPAM characterization experiment.

    This function processes the raw counts from preparing |0> and |1>
    and calculates the SPAM confusion matrix elements.

    Args:
        results: The list of result objects returned by the Runner. Each object
                 is a tuple of (counts, metadata).
        qubits: The list of qubits that were characterized.

    Returns:
        A dictionary containing the calculated probabilities:
        'p0_given_0', 'p1_given_0', 'p0_given_1', 'p1_given_1'.
        Returns a dictionary with an 'error' key if analysis fails.
    """
    if len(qubits) != 1:
        return {'error': 'SPAM analysis currently supports only a single qubit.'}

    analysis_results = {}
    
    if len(results) != 2:
        return {
            'error': f'Expected results for 2 circuits (prep 0 and prep 1), but received {len(results)}.'
        }

    for backend_result in results:
        if not isinstance(backend_result, tuple) or len(backend_result) != 2:
            return {'error': 'Result object is not a valid (counts, metadata) tuple.'}

        counts = backend_result[0]
        metadata = backend_result[1]

        total_shots = sum(counts.values())
        if total_shots == 0:
            continue

        ideal_state = metadata.get('ideal_state')
        
        # This is the block where the IndentationError occurred.
        # The 'return' statement below MUST be indented.
        if ideal_state not in ['0', '1']:
            return {'error': f"Invalid 'ideal_state' in metadata: {ideal_state}"}

        # Calculate the probabilities based on the prepared state
        if ideal_state == '0':
            # We prepared |0>
            analysis_results['p0_given_0'] = counts.get('0', 0) / total_shots
            analysis_results['p1_given_0'] = counts.get('1', 0) / total_shots
        elif ideal_state == '1':
            # We prepared |1>
            analysis_results['p0_given_1'] = counts.get('0', 0) / total_shots
            analysis_results['p1_given_1'] = counts.get('1', 0) / total_shots

    # Final check to ensure all probabilities were calculated
    required_keys = {'p0_given_0', 'p1_given_0', 'p0_given_1', 'p1_given_1'}
    if not required_keys.issubset(analysis_results.keys()):
        return {'error': 'Analysis failed to produce all required probabilities. Check experiment results.'}

    return analysis_results