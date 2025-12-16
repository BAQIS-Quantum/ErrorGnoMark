# File Path: src/egm/reporting/formatters/table_formatter.py
"""
Functions for formatting structured result data into human-readable text tables.
"""

from typing import Union
from egm.schemas.results.base import BaseAnalysisResult
from egm.schemas.results.rb import RBAnalysisResult
from egm.schemas.results.tomo import QSTAnalysisResult, QPTAnalysisResult

# A type hint for any of our analysis result models
AnyAnalysisResult = Union[RBAnalysisResult, QSTAnalysisResult, QPTAnalysisResult]

def format_result_summary(result: AnyAnalysisResult) -> str:
    """
    Creates a formatted string summary for any supported result data model.

    This function acts as a dispatcher, calling the appropriate specific
    formatting function based on the type of the result object.

    Args:
        result: An analysis result object inheriting from BaseAnalysisResult.

    Returns:
        A formatted string containing key metrics.
    """
    if isinstance(result, RBAnalysisResult):
        return _format_rb_summary(result)
    elif isinstance(result, QSTAnalysisResult):
        return _format_qst_summary(result)
    elif isinstance(result, QPTAnalysisResult):
        return _format_qpt_summary(result)
    else:
        return _format_generic_summary(result)

def _format_rb_summary(result: RBAnalysisResult) -> str:
    header = f"--- RB Analysis (Qubits: {result.qubits}) ---"
    lines = [header]
    if result.success and result.epc is not None:
        epc_err_str = f"± {result.epc_error:.2e}" if result.epc_error is not None else ""
        lines.append(f"  Error Per Clifford (EPC): {result.epc:.3e} {epc_err_str}")
        
        alpha_param = result.alpha
        if alpha_param:
            alpha_err_str = f"± {alpha_param.std_dev:.2e}" if alpha_param.std_dev is not None else ""
            lines.append(f"  Depolarization (p): {alpha_param.value:.6f} {alpha_err_str}")
    else:
        lines.append("  Analysis failed or EPC could not be computed.")
    
    lines.append("-" * len(header))
    return "\n".join(lines)

def _format_qst_summary(result: QSTAnalysisResult) -> str:
    header = f"--- QST Analysis (Qubits: {result.qubits}) ---"
    lines = [header]
    if result.success:
        lines.append(f"  State Fidelity: {result.fidelity:.6f}")
    else:
        lines.append("  Analysis failed.")
    lines.append("-" * len(header))
    return "\n".join(lines)

def _format_qpt_summary(result: QPTAnalysisResult) -> str:
    header = f"--- QPT Analysis (Qubits: {result.qubits}) ---"
    lines = [header]
    if result.success:
        lines.append(f"  Process Fidelity: {result.process_fidelity:.6f}")
    else:
        lines.append("  Analysis failed.")
    lines.append("-" * len(header))
    return "\n".join(lines)

def _format_generic_summary(result: BaseAnalysisResult) -> str:
    header = f"--- {result.analysis_type} Analysis (Qubits: {result.qubits}) ---"
    lines = [
        header,
        f"  Success: {result.success}",
        f"  Result ID: {result.result_id}",
        "-" * len(header)
    ]
    return "\n".join(lines)