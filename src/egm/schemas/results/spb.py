# =============================================================================
# File: egm/schemas/results/spb.py
# Version: v5.1.0 – HTML-compatible & RB‑Schema Unified
# Author : OpenAI‑Assistant
# =============================================================================
"""
egm.schemas.results.spb
=======================

Schema definitions for Speckle‑Purity Benchmarking (SPB) analysis results.
Fully compatible with RB/SPB/XEB report and visualization systems (Pydantic v2+).
"""

from __future__ import annotations
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, model_validator
import uuid


# ---------------------------------------------------------------------------
# SPB Fit Parameter Container
# ---------------------------------------------------------------------------
class SPBFitParameters(BaseModel):
    """Container for parameters derived from exponential SPB decay fitting."""

    A: float = Field(..., description="Amplitude of the exponential SPB decay")
    p_c: float = Field(..., description="Per‑cycle purity decay parameter")
    B: float = Field(..., description="Offset value (asymptotic purity)")
    r_squared: Optional[float] = Field(default=None, description="Coefficient of determination (R²) for fit")
    stderr: Dict[str, float] = Field(default_factory=dict, description="Standard errors of each parameter")
    success: bool = Field(default=True, description="Indicates fit convergence result")
    message: Optional[str] = Field(default=None, description="Optional diagnostic message from fitting routine")

    class Config:
        title = "SPBFitParameters"
        extra = "ignore"
        arbitrary_types_allowed = True


# ---------------------------------------------------------------------------
# SPB Analysis Result Schema (主类)
# ---------------------------------------------------------------------------
class SPBAnalysisResult(BaseModel):
    """
    Structured output of a complete SPB analysis.
    Used by report generators and visualization modules.
    """

    # ---- Metadata ----
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()),
                           description="Unique identifier for this analysis result")
    analysis_type: str = Field(default="SPB", description="Type identifier for the analysis result")
    success: bool = Field(default=True, description="Overall fit success status, mirrors fit.success")

    # ---- Core data ----
    qubits: Optional[List[int]] = Field(None, description="List of qubit indices involved in the experiment")
    axis_mode: str = Field(default="depth", description="Axis label mode: 'depth' or 'gate_count'")
    depths: List[int] = Field(default_factory=list, description="Circuit depths or gate counts analyzed")
    mean_purity: List[float] = Field(default_factory=list, description="Average measured purity per depth")
    error_bar: List[float] = Field(default_factory=list, description="Associated error bar values")
    fit: SPBFitParameters = Field(..., description="SPB exponential fit results and diagnostic info")

    # ---- Model-level validation ----
    @model_validator(mode="after")
    def sync_success(self):
        """Automatically mirror the nested fit.success field."""
        if hasattr(self, "fit") and getattr(self.fit, "success", None) is not None:
            self.success = self.fit.success
        return self

    # ---- Derived shortcut attributes for HTML / legacy templates ----
    @property
    def p_c(self) -> Optional[float]:
        """Expose per‑cycle purity decay directly for templates expecting result.p_c"""
        try:
            return self.fit.p_c
        except Exception:
            return None

    @property
    def r_squared(self) -> Optional[float]:
        """Expose R² fitting metric for direct template access."""
        try:
            return self.fit.r_squared
        except Exception:
            return None

    @property
    def A(self) -> Optional[float]:
        """Expose amplitude."""
        try:
            return self.fit.A
        except Exception:
            return None

    @property
    def B(self) -> Optional[float]:
        """Expose offset."""
        try:
            return self.fit.B
        except Exception:
            return None

    class Config:
        title = "SPBAnalysisResult"
        extra = "ignore"
        arbitrary_types_allowed = True