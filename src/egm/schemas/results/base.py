# File: errorgnomark/schemas/results/base.py
# ---------------------------------------------------------------------
# Module: Base Analysis and Fit Schemas
# ---------------------------------------------------------------------
# Defines foundational Pydantic models used to represent the results
# of experimental analyses within the ErrorGnoMark framework.
#
# Provides:
#   • FitParameter  – represents one fitted model parameter.
#   • FitResult     – encapsulates the outcome of a full model fit.
#   • BaseAnalysisResult – universal base schema for all analysis results.
# ---------------------------------------------------------------------

from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------
# FitParameter
# ---------------------------------------------------------------------
class FitParameter(BaseModel):
    """
    Represents a single parameter from a curve‑fitting procedure.

    Attributes:
        name:      Parameter name (e.g., "A", "p", "T1").
        value:     Estimated parameter value from the fit.
        std_dev:   Optional standard deviation (uncertainty) of the parameter.
    """
    name: str = Field(
        ...,
        description="Parameter name (e.g., 'A', 'p', 'T1').",
    )
    value: float = Field(
        ...,
        description="Fitted numerical value of the parameter.",
    )
    std_dev: Optional[float] = Field(
        None,
        description="Standard deviation (1σ uncertainty) of the fitted value.",
    )


# ---------------------------------------------------------------------
# FitResult
# ---------------------------------------------------------------------
class FitResult(BaseModel):
    """
    Represents the complete result of a model‑fitting operation.

    Encapsulates all mathematical and statistical details for a given
    curve‑fit model, used by higher‑level analysis result schemas.
    """
    model_name: str = Field(
        ...,
        description=(
            "Name of the mathematical model used for the fit "
            "(e.g., 'exponential_decay', 'randomized_benchmarking')."
        ),
    )
    params: List[FitParameter] = Field(
        ...,
        description="List of all fitted model parameters with uncertainties.",
    )
    r_squared: Optional[float] = Field(
        None,
        description="Goodness‑of‑fit metric: coefficient of determination (R²).",
    )
    chi_squared: Optional[float] = Field(
        None,
        description="Goodness‑of‑fit metric: total chi‑squared (χ²) value.",
    )

    class Config:
        """Model configuration for serialization and immutability."""
        frozen = True


# ---------------------------------------------------------------------
# BaseAnalysisResult
# ---------------------------------------------------------------------
class BaseAnalysisResult(BaseModel):
    """
    Core metadata schema for any analysis result.

    All experiment‑specific result models should inherit from this
    base class to maintain traceability and structural consistency
    across the ErrorGnoMark analysis suite.

    Attributes:
        result_id:          Unique identifier for this result instance.
        plan_id:            UUID of the associated experimental plan.
        analysis_type:      Name/type of the performed analysis (e.g., "RB").
        qubits:             List of qubit indices involved.
        timestamp_analysis: UTC timestamp when the analysis completed.
        analyzer_version:   Version of analysis package used.
        raw_data_ids:       Source raw data identifiers.
        success:            Whether the analysis completed successfully.
        fit:                Optional nested FitResult containing detailed
                            curve‑fit information.
        tags:               User‑defined labels for categorization.
        notes:              Optional free‑form notes.
    """

    # --- Core Identification ---
    result_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this analysis result.",
    )
    plan_id: UUID = Field(
        ...,
        description="Identifier of the ExperimentPlan this result was derived from.",
    )
    analysis_type: str = Field(
        ...,
        description="Type of analysis performed (e.g., 'T1', 'RB').",
    )
    qubits: List[int] = Field(
        ...,
        description="List of qubit indices participating in the analysis.",
    )

    # --- Provenance and Timestamps ---
    timestamp_analysis: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp indicating when the analysis was completed.",
    )
    analyzer_version: str = Field(
        ...,
        description="Version string of the analysis software.",
    )
    raw_data_ids: List[UUID] = Field(
        ...,
        description="List of UUIDs referencing raw data sets used in the analysis.",
    )

    # --- Status and Result Data ---
    success: bool = Field(
        ...,
        description="Boolean flag indicating whether the analysis succeeded.",
    )
    fit: Optional[FitResult] = Field(
        None,
        description="Nested detailed fit results, if applicable.",
    )

    # --- Metadata and User Notes ---
    tags: List[str] = Field(
        default_factory=list,
        description="User‑defined tags for organization or search.",
    )
    notes: Optional[str] = Field(
        None,
        description="Optional free‑form notes or comments.",
    )

    class Config:
        """Pydantic model configuration for BaseAnalysisResult."""
        validate_assignment = True
        frozen = True
        json_encoders = {
            UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat() + "Z",
        }