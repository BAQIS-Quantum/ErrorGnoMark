# =============================================================================
# File: src/egm/schemas/results/rb.py
# Version: v5.2 – Unified RB Result Schema (EGM + Analysis Integration)
# Author : OpenAI‑Assistant
# =============================================================================
"""
Module: Randomized Benchmarking (RB) Result Schemas

Defines structured result models for RB analyses, including:
  • RBSequenceDataPoint – represents averaged data used in fitting.
  • RBAnalysisResult    – stores fitted parameters, EPC metrics,
                           and metadata, extending BaseAnalysisResult.

Supports construction directly from analysis layer output
(`fit_rb_data()` results) via classmethod `from_fit_dict()`.
"""

from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from egm.schemas.results.base import BaseAnalysisResult, FitResult, FitParameter


# ---------------------------------------------------------------------
# RBSequenceDataPoint
# ---------------------------------------------------------------------
class RBSequenceDataPoint(BaseModel):
    """Represents a single aggregated measurement point used for the RB fit."""
    sequence_length: int = Field(..., description="Number of Clifford gates in the sequence (m).")
    survival_probability: float = Field(..., description="Average survival probability for this sequence length.")
    std_error: Optional[float] = Field(
        None, description="Standard error of the mean of the survival probability."
    )


# ---------------------------------------------------------------------
# RBAnalysisResult
# ---------------------------------------------------------------------
class RBAnalysisResult(BaseAnalysisResult):
    """
    Results schema for Randomized Benchmarking (RB) analyses.
    Extends BaseAnalysisResult with RB‑specific sequence data and
    derived metrics such as the Error Per Clifford (EPC).
    """

    # -----------------------------------------------------------------
    # Base Required Metadata (defaults added)
    # -----------------------------------------------------------------
    plan_id: UUID = Field(default_factory=uuid4, description="Unique identifier for this RB plan instance.")
    analyzer_version: str = Field(default="2.3", description="Version of RB analyzer or pipeline.")
    raw_data_ids: List[UUID] = Field(default_factory=list, description="List of raw dataset UUIDs associated with fit.")

    # -----------------------------------------------------------------
    # Fixed Analysis Type
    # -----------------------------------------------------------------
    analysis_type: Literal["RB"] = Field(
        "RB", description="Fixed analysis type identifier for RB results."
    )

    # -----------------------------------------------------------------
    # Aggregated Data for Visualization
    # -----------------------------------------------------------------
    sequence_data: List[RBSequenceDataPoint] = Field(
        default_factory=list,
        description="List of aggregated RB data points used for exponential fitting.",
    )

    # -----------------------------------------------------------------
    # Derived Convenience Accessors
    # -----------------------------------------------------------------
    @property
    def alpha(self) -> Optional[FitParameter]:
        """Retrieve the depolarization (“p”) parameter from the fitted model."""
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
            EPC = ((2ⁿ – 1) / 2ⁿ) × (1 – p)
        """
        if not self.success or not self.alpha:
            return None
        p = self.alpha.value
        d = 2 ** len(self.qubits)
        return ((d - 1) / d) * (1 - p)

    @property
    def epc_error(self) -> Optional[float]:
        """Propagate uncertainty of the EPC."""
        if not self.success or not self.alpha or self.alpha.std_dev is None:
            return None
        d = 2 ** len(self.qubits)
        return ((d - 1) / d) * self.alpha.std_dev

    # -----------------------------------------------------------------
    # Validators
    # -----------------------------------------------------------------
    @model_validator(mode="after")
    def _check_fit_integrity(self) -> RBAnalysisResult:
        if not self.success:
            return self
        if self.success and (not self.fit or not self.alpha):
            raise ValueError(
                "RBAnalysisResult indicates success but lacks a valid fit "
                "with a depolarization parameter 'p'."
            )
        return self

    # -----------------------------------------------------------------
    # Class Construction Helper
    # -----------------------------------------------------------------
    @classmethod
    def from_fit_dict(
        cls,
        fit_dict: Dict[str, Any],
        qubits: Optional[List[int]] = None,
    ) -> "RBAnalysisResult":
        """Construct an RBAnalysisResult from a fit_rb_data() dictionary."""
        sequence_data = [
            RBSequenceDataPoint(
                sequence_length=int(d),
                survival_probability=float(m),
                std_error=float(e) if e is not None else None,
            )
            for d, m, e in zip(
                fit_dict.get("depths", []),
                fit_dict.get("means", []),
                fit_dict.get("std_errors", []),
            )
        ]

        fit_result = FitResult(
            model_name="A·p^m + B",
            params=[
                FitParameter(name="A", value=fit_dict.get("A")),
                FitParameter(name="B", value=fit_dict.get("B")),
                FitParameter(name="p", value=fit_dict.get("p")),
            ],
            metrics={"r_squared": fit_dict.get("r_squared")},
            success=fit_dict.get("fit_successful", False),
        )

        return cls(
            plan_id=uuid4(),
            analyzer_version="2.3",
            raw_data_ids=[uuid4()],
            success=fit_dict.get("fit_successful", False),
            fit=fit_result,
            sequence_data=sequence_data,
            qubits=qubits or [],
        )

    # -----------------------------------------------------------------
    # Debug Representation
    # -----------------------------------------------------------------
    def __repr__(self) -> str:
        q_str = ",".join(map(str, self.qubits)) if self.qubits else "-"
        epc_val = f"{self.epc:.3e}" if self.epc is not None else "None"
        return f"<RBAnalysisResult qubits=[{q_str}] success={self.success} EPC={epc_val}>"

    # -----------------------------------------------------------------
    # Pydantic Config
    # -----------------------------------------------------------------
    model_config = {
        "computed_fields": {
            "epc": {"description": "Computed Error Per Clifford (EPC)."},
            "epc_error": {"description": "Uncertainty for EPC."},
        },
    }

# =============================================================================
# End of File
# =============================================================================