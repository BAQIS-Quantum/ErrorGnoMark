from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TaskAnalysisResult:
    plan_id: str
    task_id: str
    status: str  # "ok" | "analysis_error"
    error: Optional[str] = None
    analysis_payload: Dict[str, Any] = field(default_factory=dict)

