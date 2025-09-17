# File Path: errorgnomark/analysis/analysis_results.py
# This new file breaks the circular import by providing a neutral location
# for the shared AnalysisResult data structure.

from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class AnalysisResult:
    """
    A data class to hold the results of a state tomography analysis.
    This acts as a standardized container for passing data from the
    analysis step to the reporting step.
    """
    analysis_type: str
    method: str
    reconstructed_rho: np.ndarray
    fidelity_with_ideal: Optional[float] = None
    purity: Optional[float] = None
    trace: Optional[float] = None