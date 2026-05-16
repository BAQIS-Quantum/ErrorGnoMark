# =============================================================================
# File: src/egm/schemas/results/prb.py
# Version: v5.0 – Unified PRB Result Schema (EGM + Analysis Integration)
# =============================================================================
"""
Purity Randomized Benchmarking (PRB) Result Schemas

Defines structured result models for PRB analyses, including:
  • PRBSequenceDataPoint — calibrated purity‑per‑depth record.
  • PRBAnalysisResult    — full fitted analysis result with metrics.

Mirrors the structure of `RBAnalysisResult` for uniformity.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from egm.schemas.results.base import BaseAnalysisResult, FitParameter, FitResult


# ---------------------------------------------------------------------
# PRBSequenceDataPoint
# ---------------------------------------------------------------------
class PRBSequenceDataPoint(BaseModel):
    """
    Represents one averaged calibrated purity data point in PRB fitting.
    """

    sequence_length: int = Field(..., description="Number of Cliffords (m) in the sequence.")
    calibrated_purity: float = Field(..., description="Mean calibrated purity (P−B)/A at this depth.")
    std_error: Optional[float] = Field(None, description="Standard error for the calibrated purity.")


# ---------------------------------------------------------------------
# PRBAnalysisResult
# ---------------------------------------------------------------------
class PRBAnalysisResult(BaseAnalysisResult):
    """
    Structured analysis result for Purity RB (PRB) experiments.

    Contains calibrated sequence data and fitted parameters
    (A, B, α) describing purity decay over Clifford depth.
    """

    analysis_type: Literal["PRB"] = Field("PRB", description="Result type identifier for PRB analyses.")

    sequence_data: List[PRBSequenceDataPoint] = Field(
        ..., description="List of calibrated purity data points used for exponential fitting."
    )

    # -----------------------------------------------------------------
    # Derived computed properties
    # -----------------------------------------------------------------
    @property
    def alpha(self) -> Optional[FitParameter]:
        """Return the fitted decay parameter α."""
        if self.fit:
            for param in self.fit.params:
                if param.name == "alpha":
                    return param
        return None

    @property
    def gate_error(self) -> Optional[float]:
        """
        Compute the derived interleaved‑gate error if available.
        This field may be filled later by workflow composition.
        """
        if getattr(self, "_gate_error", None) is not None:
            return self._gate_error
        return None

    # Optional setter so the suites layer can attach results
    def set_gate_error(self, value: float) -> None:
        object.__setattr__(self, "_gate_error", value)

    # -----------------------------------------------------------------
    # Validator
    # -----------------------------------------------------------------
    @model_validator(mode="after")
    def _check_fit_integrity(self) -> PRBAnalysisResult:
        """Ensure validity of fitted α when success=True."""
        if not self.success:
            return self
        if self.success and (not self.fit or not self.alpha):
            raise ValueError(
                "PRBAnalysisResult indicates success but lacks a valid 'alpha' "
                "depolarization parameter."
            )
        return self

    # -----------------------------------------------------------------
    # Factory Method
    # -----------------------------------------------------------------
    @classmethod
    def from_fit_dict(
        cls,
        fit_dict: Dict[str, Any],
        qubits: Optional[List[int]] = None,
    ) -> PRBAnalysisResult:
        """
        Construct a PRBAnalysisResult from a fit_prb_data() dictionary.

        Args:
            fit_dict: Result dict returned from analysis.fit_prb_data().
            qubits:   List of qubit identifiers used in this PRB experiment.

        Returns:
            PRBAnalysisResult instance ready for reporting.
        """
        sequence_data = [
            PRBSequenceDataPoint(
                sequence_length=int(d),
                calibrated_purity=float(m),
                std_error=float(e) if e is not None else None,
            )
            for d, m, e in zip(
                fit_dict.get("depths", []),
                fit_dict.get("calibrated_mean_purities", []),
                fit_dict.get("calibrated_std_errors", []),
            )
        ]

        fit_result = FitResult(
            model_name="A·α^m + B",
            params=[
                FitParameter(name="A", value=fit_dict.get("A")),
                FitParameter(name="B", value=fit_dict.get("B")),
                FitParameter(name="alpha", value=fit_dict.get("alpha")),
            ],
            metrics={"success": fit_dict.get("fit_successful", False)},
            success=fit_dict.get("fit_successful", False),
        )

        return cls(
            success=fit_dict.get("fit_successful", False),
            fit=fit_result,
            sequence_data=sequence_data,
            qubits=qubits or [],
        )

    # -----------------------------------------------------------------
    # Representation
    # -----------------------------------------------------------------
    def __repr__(self) -> str:
        q_str = ",".join(map(str, self.qubits)) if self.qubits else "-"
        alpha_val = self.alpha.value if self.alpha else None
        return f"<PRBAnalysisResult qubits=[{q_str}] success={self.success} α={alpha_val}>"

    class Config(BaseAnalysisResult.Config):
        """Enable computed‑field serialization."""
        computed_fields = {
            "alpha": {"description": "Fitted purity decay parameter (α)."},
            "gate_error": {"description": "Interleaved‑gate error if provided."},
        }

# =============================================================================
# End of File
# =============================================================================