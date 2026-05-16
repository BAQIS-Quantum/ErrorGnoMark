# =============================================================================
# File    : egm/schemas/results/xeb.py
# Version : v5.1.0 - HTML-compatible & RB-Schema Unified
# Author  : OpenAI-Assistant
# =============================================================================
"""
egm.schemas.results.xeb
=======================

Schema definitions for Cross-Entropy Benchmarking (XEB) analysis results.
Fully compatible with RB/XEB/SPB unified report generators (Pydantic v2+).
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# XEB Fit Parameter Container
# ---------------------------------------------------------------------------
class XEBFitParameters(BaseModel):
    """Container for parameters obtained from exponential XEB decay fitting."""

    A: float = Field(..., description="Amplitude of the exponential decay.")
    p: float = Field(..., description="Decay parameter per circuit depth.")
    B: float = Field(..., description="Offset (asymptotic fidelity).")
    epc: float = Field(..., description="Estimated error per Clifford (EPC).")
    r_squared: Optional[float] = Field(
        default=None,
        description="Coefficient of determination (R^2) for exponential fit.",
    )
    stderr: Dict[str, float] = Field(
        default_factory=dict,
        description="Standard errors for each fit parameter.",
    )
    success: bool = Field(default=True, description="Indicates fit convergence result.")
    message: Optional[str] = Field(
        default=None, description="Optional diagnostic message from the fitting routine."
    )

    class Config:
        title = "XEBFitParameters"
        extra = "ignore"
        arbitrary_types_allowed = True


# ---------------------------------------------------------------------------
# XEB Analysis Result Schema (Main Class)
# ---------------------------------------------------------------------------
class XEBAnalysisResult(BaseModel):
    """
    Structured output of a full XEB analysis for standardized reporting.

    Provides compatibility with RB-style report generators and schema systems.
    """

    # ---- Report metadata ----
    result_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this analysis result.",
    )
    analysis_type: str = Field(
        default="XEB", description="Type identifier for this analysis result."
    )
    success: bool = Field(
        default=True,
        description="Overall fit success status, mirrors fit.success.",
    )

    # ---- Core attributes ----
    qubits: Optional[List[int]] = Field(
        None, description="List of qubit indices used in the experiment."
    )
    axis_mode: str = Field(
        default="depth", description="Axis label mode: 'depth' or 'gate_count'."
    )
    depths: List[int] = Field(
        default_factory=list, description="Evaluated circuit depths."
    )
    mean_fidelity: List[float] = Field(
        default_factory=list, description="Average fidelity at each depth."
    )
    error_bar: List[float] = Field(
        default_factory=list, description="Associated error bar values per depth."
    )
    fit: XEBFitParameters = Field(
        ..., description="Fitted parameters and diagnostic information."
    )

    # ------------------------------------------------------------------
    # Model-level validation (Pydantic v2)
    # ------------------------------------------------------------------
    @model_validator(mode="after")
    def sync_success(self):
        """Automatically mirror the nested fit.success field."""
        if hasattr(self, "fit") and getattr(self.fit, "success", None) is not None:
            self.success = self.fit.success
        return self

    # ------------------------------------------------------------------
    # Derived shortcut attributes for HTML / legacy templates
    # ------------------------------------------------------------------
    @property
    def epc(self) -> Optional[float]:
        """Expose EPC directly for RB/XEB HTML templates expecting result.epc."""
        try:
            return self.fit.epc
        except Exception:
            return None

    @property
    def p(self) -> Optional[float]:
        """Expose decay parameter directly (template expects result.p)."""
        try:
            return self.fit.p
        except Exception:
            return None

    @property
    def r_squared(self) -> Optional[float]:
        """Expose R^2 directly for quick access in templates."""
        try:
            return self.fit.r_squared
        except Exception:
            return None

    class Config:
        title = "XEBAnalysisResult"
        extra = "ignore"
        arbitrary_types_allowed = True