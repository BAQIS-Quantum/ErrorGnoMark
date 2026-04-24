# File: errorgnomark/reporting/generators/terminal_generator.py
# ---------------------------------------------------------------------
# Module: TerminalReportGenerator — Console Summary Renderer
# ---------------------------------------------------------------------
# Provides a simple, readable console summary for experiment analysis
# results. This is typically used for quick inspection following
# automated or manual experiment runs.
#
# Integrates with:
#   • reporting.formatters.table_formatter.format_result_summary
#   • schemas.results.* (via AnyAnalysisResult type alias)
# ---------------------------------------------------------------------

from __future__ import annotations
from typing import List, Dict, Any
from egm.reporting.formatters.table_formatter import (
    format_result_summary,
    AnyAnalysisResult,
)


# ---------------------------------------------------------------------
# Public Interface
# ---------------------------------------------------------------------
def generate_terminal_report(
    analysis_results: List[AnyAnalysisResult],
    experiment_params: Dict[str, Any],
) -> None:
    """
    Print a formatted analysis summary directly to the terminal.

    This function displays high‑level experiment parameters followed by
    a series of formatted result summaries.

    Args:
        analysis_results:
            List of analysis result objects (e.g., RBAnalysisResult).
        experiment_params:
            Dictionary of global experiment metadata, such as workflow
            labels, qubit count, or execution configuration.
    """
    print("\n" + "=" * 64)
    print(" " * 20 + "EXPERIMENT ANALYSIS REPORT")
    print("=" * 64)

    # ---------------------------------------------------------------
    # Experiment Parameters
    # ---------------------------------------------------------------
    print("\n[ Experiment Parameters ]")
    if not experiment_params:
        print("  (None provided)")
    else:
        for key, value in experiment_params.items():
            print(f"  - {key}: {value}")

    # ---------------------------------------------------------------
    # Analysis Results
    # ---------------------------------------------------------------
    print("\n[ Analysis Results ]")
    if not analysis_results:
        print("  No analysis results available.")
    else:
        for idx, result in enumerate(analysis_results, start=1):
            print(f"\n--- Result {idx} ---")
            print(format_result_summary(result))

    print("\n" + "=" * 64)
    print("End of Analysis Report")
    print("=" * 64 + "\n")