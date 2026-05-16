# =============================================================================
# File: egm/schemas/results/csb.py
# Version: v3.1 – CSB Result Schema (Spectral, Status‑Aware)
# =============================================================================
"""
Channel Spectrum Benchmarking (CSB) Result Schemas

CSB is a spectral analysis method:
  • No curve fitting
  • No RB-style exponential decay assumption
  • Spectral quantities may be partially available
"""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from egm.schemas.results.base import BaseAnalysisResult


# =============================================================================
# Analysis Status
# =============================================================================
class AnalysisStatus(str, Enum):
    """
    Lifecycle status of an analysis result.
    """
    SUCCESS = "success"     # Spectral phase successfully extracted
    PARTIAL = "partial"     # Analysis ran, but phase not fully validated
    FAILED = "failed"       # Analysis failed or invalid


# =============================================================================
# CSBSequenceDataPoint
# =============================================================================
class CSBSequenceDataPoint(BaseModel):
    """
    Aggregated CSB probability vs effective sequence length.
    """
    sequence_length: int = Field(
        ...,
        description="Effective CSB sequence length (depth × repetition)."
    )
    probability: float = Field(
        ...,
        description="Average measured probability."
    )
    std_error: Optional[float] = Field(
        None,
        description="Standard error of the mean."
    )


# =============================================================================
# CSBAnalysisResult
# =============================================================================
class CSBAnalysisResult(BaseAnalysisResult):
    """
    Result schema for Channel Spectrum Benchmarking (CSB).

    CSB does not guarantee availability of all physical metrics.
    Completeness is explicitly encoded via `status`.
    """

    # -----------------------------------------------------------------
    # Fixed Analysis Type
    # -----------------------------------------------------------------
    analysis_type: Literal["CSB"] = Field(
        "CSB",
        description="Fixed analysis type identifier for CSB."
    )

    # -----------------------------------------------------------------
    # Analysis Lifecycle Status
    # -----------------------------------------------------------------
    status: AnalysisStatus = Field(
        ...,
        description="Lifecycle status of the CSB analysis."
    )

    # -----------------------------------------------------------------
    # Aggregated Spectral Data (optional, for visualization/debug)
    # -----------------------------------------------------------------
    sequence_data: List[CSBSequenceDataPoint] = Field(
        default_factory=list,
        description="Aggregated CSB probability data vs sequence length."
    )

    # -----------------------------------------------------------------
    # Spectral / Physical Metrics (all optional by design)
    # -----------------------------------------------------------------
    decay: Optional[float] = Field(
        None,
        description="Magnitude of dominant eigenvalue |λ|, if extracted."
    )
    phase: Optional[float] = Field(
        None,
        description="Extracted spectral phase φ (radians)."
    )
    phase_error: Optional[float] = Field(
        None,
        description="Phase error relative to target phase."
    )
    stochastic_infidelity: Optional[float] = Field(
        None,
        description="Stochastic infidelity inferred from spectral decay."
    )
    process_infidelity: Optional[float] = Field(
        None,
        description="Estimated total process infidelity."
    )

    # -----------------------------------------------------------------
    # Integrity Validation
    # -----------------------------------------------------------------
    @model_validator(mode="after")
    def _check_integrity(self) -> CSBAnalysisResult:
        """
        Enforce minimal physical completeness when status == SUCCESS.

        SUCCESS means:
            • spectral phase is uniquely determined
        """
        if self.status is not AnalysisStatus.SUCCESS:
            return self

        # ✅ Only phase is strictly required for SUCCESS
        if self.phase is None:
            raise ValueError(
                "CSBAnalysisResult marked SUCCESS but missing required metric: phase"
            )

        return self

    # -----------------------------------------------------------------
    # Debug Representation
    # -----------------------------------------------------------------
    def __repr__(self) -> str:
        if self.status is not AnalysisStatus.SUCCESS:
            return f"<CSBAnalysisResult status={self.status}>"
        return (
            "<CSBAnalysisResult "
            f"phase={self.phase:.6f} "
            f"phase_error={self.phase_error:.3e}>"
        )


# =============================================================================
# End of File
# =============================================================================