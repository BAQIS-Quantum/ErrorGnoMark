# =============================================================================
# File: errorgnomark/schemas/results/base.py
# Version: v5.2 – Core Schema Definitions (Mutable Edition)
# =============================================================================
"""
Module: Base Analysis and Fit Schemas

Defines foundational Pydantic models used to represent the results
of experimental analyses within the ErrorGnoMark framework.

Provides:
  • FitParameter  – represents one fitted model parameter.
  • FitResult     – encapsulates the outcome of a full model fit.
  • BaseAnalysisResult – universal base schema for all analysis results.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------
# FitParameter
# ---------------------------------------------------------------------
class FitParameter(BaseModel):
    """Represents a single parameter from a curve‑fitting procedure."""
    name: str = Field(..., description="Parameter name (e.g., 'A', 'p', 'T1').")
    value: float = Field(..., description="Fitted numerical value of the parameter.")
    std_dev: Optional[float] = Field(
        None, description="Standard deviation (1σ uncertainty) of the fitted value."
    )


# ---------------------------------------------------------------------
# FitResult
# ---------------------------------------------------------------------
class FitResult(BaseModel):
    """
    Represents the complete result of a model‑fitting operation.
    Includes model name, parameters, metrics, and success flag.
    """
    model_name: str = Field(..., description="Name of the mathematical model used for the fit.")
    params: List[FitParameter] = Field(..., description="List of all fitted model parameters.")
    r_squared: Optional[float] = Field(None, description="Coefficient of determination (R²).")
    chi_squared: Optional[float] = Field(None, description="Total chi‑squared (χ²) value.")
    success: bool = Field(default=False, description="Whether the fitting operation succeeded.")

    class Config:
        validate_assignment = True   # allow field updates
        frozen = False               # model instances can be modified


# ---------------------------------------------------------------------
# BaseAnalysisResult
# ---------------------------------------------------------------------
class BaseAnalysisResult(BaseModel):
    """
    Core metadata schema for any analysis result.

    All experiment‑specific result models should inherit from this
    base class to maintain traceability and structural consistency.
    """
    # --- Core Identification ---
    result_id: UUID = Field(default_factory=uuid4, description="Unique identifier for this analysis result.")
    plan_id: UUID = Field(..., description="Identifier of the ExperimentPlan this result was derived from.")
    analysis_type: str = Field(..., description="Type of analysis performed (e.g., 'T1', 'RB').")
    qubits: List[int] = Field(..., description="List of qubit indices participating in the analysis.")

    # --- Provenance and Timestamps ---
    timestamp_analysis: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp indicating when the analysis was completed.",
    )
    analyzer_version: str = Field(..., description="Version string of the analysis software.")
    raw_data_ids: List[UUID] = Field(..., description="UUIDs of raw data sets used in the analysis.")

    # --- Status and Result Data ---
    success: bool = Field(..., description="Whether the analysis succeeded.")
    fit: Optional[FitResult] = Field(None, description="Detailed fit results, if applicable.")

    # --- Metadata and User Notes ---
    tags: List[str] = Field(default_factory=list, description="User‑defined tags for organization or search.")
    notes: Optional[str] = Field(None, description="Optional notes or comments.")

    class Config:
        validate_assignment = True   # allow safe updates post‑creation
        frozen = False               # must be mutable for runtime field updates
        json_encoders = {
            UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat() + "Z",
        }