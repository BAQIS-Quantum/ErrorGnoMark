# errorgnomark/analysis/characterization/results.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np

@dataclass
class BaseAnalysisResult:
    """
    Base class for all analysis results.
    The rule for dataclass inheritance is that non-default fields in child classes
    cannot follow default fields in base classes.
    The fix is to put all required fields here in the base class, without defaults.
    """
    # --- REQUIRED fields first ---
    # 'qubits' is a required field for all result types.
    # For single-qubit experiments, this will be a list with one element (e.g., [0]).
    qubits: List[int]

    # --- OPTIONAL fields (with defaults) after ---
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FidelityAnalysisResult(BaseAnalysisResult):
    """
    Holds the results of a fidelity analysis, such as from Pauli Twirling.
    Inherits 'qubits' as a required field. All fields defined here are optional.
    """
    gate_name: Optional[str] = None
    fidelity: float = -1.0
    fidelity_stderr: float = -1.0


@dataclass
class CoherenceAnalysisResult(BaseAnalysisResult):
    """
    Holds the results of a coherence time experiment (T1, T2, T2*).
    Inherits 'qubits' as a required field.
    """
    coherence_time: float = -1.0
    coherence_time_stderr: float = -1.0
    unit: str = 's'
    fit_function: str = ""
    fit_parameters: Dict[str, float] = field(default_factory=dict)
    fit_parameters_stderr: Dict[str, float] = field(default_factory=dict)


@dataclass
class SpamAnalysisResult(BaseAnalysisResult):
    """
    Holds the results of a State Preparation and Measurement (SPAM) analysis.
    Inherits 'qubits' as a required field.
    """
    spam_matrix: np.ndarray = field(default_factory=lambda: np.full((2, 2), -1.0))
    readout_fidelity: float = -1.0


@dataclass
class StateTomographyAnalysisResult(BaseAnalysisResult):
    """
    Holds the results of a quantum state tomography analysis.
    Inherits 'qubits' as a required field.
    """
    reconstructed_density_matrix: np.ndarray = field(default_factory=lambda: np.array([[]]))
    state_fidelity: float = -1.0
    purity: float = -1.0
    ideal_state_label: Optional[str] = None