# File: errorgnomark/schemas/results/rb.py
# ---------------------------------------------------------------------
# Module: Randomized Benchmarking (RB) Result Schemas
# ---------------------------------------------------------------------
# Defines structured result models for RB analyses, including:
#   • RBSequenceDataPoint – represents averaged data used in fitting.
#   • RBAnalysisResult    – stores fitted parameters, EPC metrics,
#                            and metadata, extending BaseAnalysisResult.
#
# This module is Pydantic v2‑compliant and designed for integration
# with the reporting and visualization subsystems.
# ---------------------------------------------------------------------

from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator

from egm.schemas.results.base import BaseAnalysisResult, FitResult, FitParameter


# ---------------------------------------------------------------------
# RBSequenceDataPoint
# ---------------------------------------------------------------------
class RBSequenceDataPoint(BaseModel):
    """
    Represents a single aggregated measurement point used for the RB fit.

    Attributes:
        sequence_length:
            Number of Clifford cycles (m) composing the RB sequence.
        survival_probability:
            Averaged ground‑state survival probability at this depth.
        std_error:
            Estimated standard error of the mean for the probability.
    """

    sequence_length: int = Field(
        ...,
        description="Number of Clifford gates in the sequence (m).",
    )
    survival_probability: float = Field(
        ...,
        description="Average survival probability for this sequence length.",
    )
    std_error: Optional[float] = Field(
        None,
        description="Standard error of the mean of the survival probability.",
    )


# ---------------------------------------------------------------------
# RBAnalysisResult
# ---------------------------------------------------------------------
class RBAnalysisResult(BaseAnalysisResult):
    """
    Results schema for Randomized Benchmarking (RB) analyses.

    Extends BaseAnalysisResult with RB‑specific sequence data and
    derived metrics such as the Error Per Clifford (EPC).

    Computed properties (`epc`, `epc_error`) are exposed automatically
    during serialization via Pydantic’s computed_fields mechanism.
    """

    # -----------------------------------------------------------------
    # Fixed Analysis Type
    # -----------------------------------------------------------------
    analysis_type: Literal["RB"] = Field(
        "RB",
        description="Fixed analysis type identifier for RB results.",
    )

    # -----------------------------------------------------------------
    # Aggregated Data for Visualization
    # -----------------------------------------------------------------
    sequence_data: List[RBSequenceDataPoint] = Field(
        ...,
        description="List of aggregated RB data points used for exponential fitting.",
    )

    # -----------------------------------------------------------------
    # Derived Convenience Accessors
    # -----------------------------------------------------------------
    @property
    def alpha(self) -> Optional[FitParameter]:
        """
        Retrieve the depolarization (“p”) parameter from the fitted model.

        Returns:
            The FitParameter instance corresponding to 'p', or None.
        """
        if self.fit:
            for param in self.fit.params:
                if param.name == "p":
                    return param
        return None

    @property
    def epc(self) -> Optional[float]:
        """
        Calculate the Error Per Clifford (EPC).

        Formula:
            EPC = ((2ⁿ – 1) / 2ⁿ) × (1 – p),
        where p is the depolarization parameter from the fitted model.
        """
        if not self.success or not self.alpha:
            return None

        p = self.alpha.value
        d = 2 ** len(self.qubits)
        return ((d - 1) / d) * (1 - p)

    @property
    def epc_error(self) -> Optional[float]:
        """
        Estimate the propagated uncertainty of the EPC.

        Formula:
            σ₍EPC₎ = ((2ⁿ – 1) / 2ⁿ) × σ₍p₎,
        where σ₍p₎ is the standard deviation of the fitted parameter p.
        """
        if not self.success or not self.alpha or self.alpha.std_dev is None:
            return None

        d = 2 ** len(self.qubits)
        return ((d - 1) / d) * self.alpha.std_dev

    # -----------------------------------------------------------------
    # Validators
    # -----------------------------------------------------------------
    @model_validator(mode="after")
    def _check_fit_integrity(self) -> RBAnalysisResult:
        """
        Ensure that a successful analysis includes a valid fit
        containing the parameter 'p'.
        """
        if self.success and (not self.fit or not self.alpha):
            raise ValueError(
                "RBAnalysisResult indicates success but lacks a valid fit "
                "with a depolarization parameter 'p'."
            )
        return self

    # -----------------------------------------------------------------
    # Pydantic Config
    # -----------------------------------------------------------------
    class Config(BaseAnalysisResult.Config):
        """Configuration enabling serialization of computed fields."""
        computed_fields = {
            "epc": {"description": "Computed Error Per Clifford (EPC)."},
            "epc_error": {"description": "Uncertainty for the computed EPC."},
        }