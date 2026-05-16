# File Path: src/egm/schemas/results/tomo.py
"""
Defines Pydantic schemas for Tomography (QST/QPT) analysis results.
"""

from typing import Any, Literal

import numpy as np
from pydantic import Field

from .base import BaseAnalysisResult


class NumpyArray(np.ndarray):
    """Custom Pydantic type for numpy arrays to allow validation."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> np.ndarray:
        if not isinstance(v, np.ndarray):
            raise TypeError('numpy.ndarray required')
        return v

    class Config:
        arbitrary_types_allowed = True

class QSTAnalysisResult(BaseAnalysisResult):
    """Schema for storing Quantum State Tomography results."""
    analysis_type: Literal["QST"] = Field("QST", description="Fixed type for Quantum State Tomography analysis.")
    
    # --- QST Specific Data ---
    density_matrix: NumpyArray = Field(..., description="The reconstructed density matrix (rho).")
    fidelity: float = Field(..., description="Fidelity of the reconstructed state with the ideal target state.")

    class Config(BaseAnalysisResult.Config):
        arbitrary_types_allowed = True
        computed_fields = {} # No computed fields for QST

class QPTAnalysisResult(BaseAnalysisResult):
    """Schema for storing Quantum Process Tomography results."""
    analysis_type: Literal["QPT"] = Field("QPT", description="Fixed type for Quantum Process Tomography analysis.")

    # --- QPT Specific Data ---
    chi_matrix: NumpyArray = Field(..., description="The reconstructed process matrix (Chi).")
    process_fidelity: float = Field(..., description="Fidelity of the reconstructed process with the ideal target process.")

    class Config(BaseAnalysisResult.Config):
        arbitrary_types_allowed = True
        computed_fields = {} # No computed fields for QPT