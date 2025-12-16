# src/egm/core/data/models.py

"""
Pydantic models for data storage and exchange within the ErrorGnoMark framework.

These models define the structured format for storing experimental data,
including metadata, parameters, and results. Using Pydantic ensures that all
data passed between components (execution, analysis, reporting) is validated 
and conforms to a consistent schema. This is the single source of truth for
our data structures.
"""

# -------------------------------------------------------------------
# 1. Standard Library Imports
# -------------------------------------------------------------------
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

# -------------------------------------------------------------------
# 2. Third-Party Imports
# -------------------------------------------------------------------
from pydantic import BaseModel, Field

# ==============================================================================
# Base and Generic Models
# ==============================================================================

class BaseDataModel(BaseModel):
    """A base model with common configuration."""
    class Config:
        # Allows models to be created from ORM objects (e.g., SQLAlchemy)
        orm_mode = True
        # Use JSON encoders for types like datetime
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        # Allow extra fields to be ignored rather than raising an error
        extra = "ignore"

# ==============================================================================
# Protocol-Specific Models
# ==============================================================================

class RBParameters(BaseDataModel):
    """Parameters specific to a Randomized Benchmarking experiment."""
    qubits: List[int]
    depths: List[int]
    circuits_per_depth: int
    seed: Optional[int] = None

class RBResultData(BaseDataModel):
    """Result data from a single Randomized Benchmarking fit."""
    fit_successful: bool
    alpha: Optional[float] = Field(None, description="Decay parameter from the fit A*alpha^m + B.")
    epc: Optional[float] = Field(None, description="Error Per Clifford.")
    epg: Optional[float] = Field(None, description="Error Per Gate (if conversion is provided).")
    b_offset: Optional[float] = Field(None, description="Offset parameter from the fit A*alpha^m + B.")
    fit_parameters: Optional[List[float]] = Field(None, description="Raw parameters from the curve fit [A, alpha, B].")
    fit_covariance_matrix: Optional[List[List[float]]] = Field(None, description="Covariance matrix of the fit parameters.")
    
    # Raw data is always included for reprocessing or plotting
    raw_survival_probabilities: List[float]
    raw_std_errors: List[float]

# ==============================================================================
# Core Experiment Run Model
# ==============================================================================

class ExperimentRun(BaseDataModel):
    """
    A comprehensive model representing a single, complete experimental run.
    This is the primary object that will be saved to a database or returned to
    the user.
    """
    # --- Metadata ---
    id: UUID = Field(default_factory=uuid4)
    workflow_run_id: Optional[UUID] = Field(
        None, description="Identifier to group runs from the same workflow execution."
    )
    protocol_name: str = Field(..., description="Name of the experimental protocol, e.g., 'StandardRB'.")
    backend_name: str = Field(..., description="Name of the quantum backend used.")
    creation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    tags: Dict[str, Any] = Field(default_factory=dict, description="User-defined tags for querying.")

    # --- Data ---
    # Using Union allows for future expansion to other protocol types
    parameters: Union[RBParameters, Dict[str, Any]]
    results: Union[RBResultData, Dict[str, Any]]
    
    # --- Additional Context ---
    shots: int = Field(..., description="Number of shots used for the experiment.")
    
    def __repr__(self):
        return (
            f"ExperimentRun(id={self.id}, protocol='{self.protocol_name}', "
            f"backend='{self.backend_name}', timestamp='{self.creation_timestamp.isoformat()}')"
        )