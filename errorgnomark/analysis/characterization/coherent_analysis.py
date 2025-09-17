# errorgnomark/analysis/characterization/coherent_analysis.py

from typing import List, Dict, Any
import numpy as np
from scipy.optimize import curve_fit

from errorgnomark.analysis.results import CoherenceAnalysisResult

def _ramsey_fit_function(t, f, T2_star, A, B):
    """Decaying cosine function for fitting Ramsey experiment data."""
    return A * np.cos(2 * np.pi * f * t) * np.exp(-t / T2_star) + B

def analyze_ramsey_decay(
    delays: List[float],
    probabilities: List[float],
    qubit: int,
    unit: str = 's'
) -> CoherenceAnalysisResult:
    """
    Analyzes Ramsey experiment data to extract T2* and frequency detuning.

    Args:
        delays: A list of delay times used in the experiment.
        probabilities: The corresponding probabilities of measuring the |1> state.
        qubit: The qubit that was measured.
        unit: The time unit for the delays ('s', 'us', 'ns').

    Returns:
        A CoherenceAnalysisResult object with the fitted parameters.
    """
    x_data = np.array(delays)
    y_data = np.array(probabilities)
    
    # Provide initial guesses for the fit parameters
    f_guess = (1 / (delays[-1] - delays[0])) if len(delays) > 1 else 0.1
    T2_star_guess = np.mean(delays)
    A_guess = 0.5
    B_guess = 0.5
    p0 = [f_guess, T2_star_guess, A_guess, B_guess]

    metadata = {"unit": unit, "fit_function": "A * cos(2*pi*f*t) * exp(-t/T2*) + B"}

    try:
        params, cov = curve_fit(_ramsey_fit_function, x_data, y_data, p0=p0, maxfev=10000)
        stderr = np.sqrt(np.diag(cov))
        
        f, T2_star, A, B = params
        f_err, T2_star_err, A_err, B_err = stderr

        return CoherenceAnalysisResult(
            success=True,
            qubit=qubit,
            coherence_time=T2_star,
            coherence_time_stderr=T2_star_err,
            unit=unit,
            fit_function=metadata["fit_function"],
            fit_parameters={"frequency_detuning": f, "T2_star": T2_star, "amplitude": A, "offset": B},
            fit_parameters_stderr={"frequency_detuning_err": f_err, "T2_star_err": T2_star_err, "amplitude_err": A_err, "offset_err": B_err},
            metadata=metadata
        )
    except Exception as e:
        return CoherenceAnalysisResult(success=False, error_message=str(e), qubit=qubit, metadata=metadata)