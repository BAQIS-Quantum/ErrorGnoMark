"""
analysis/analysis_factory.py

Script Functionality:
This module defines the Application level Analytics Factory. 
It receives logically grouped raw experimental data from the execution runner 
and routes it to the specific analytical operators (Analyzers) based on protocol.

Logical Architecture:
- BaseAnalyzer: Abstract constraint guaranteeing expected input/outputs.
- Protocol Analyzers (RB, XEB): Specific algorithms wrapping legacy mathematical blocks.
- AnalysisFactory: A central task dispatcher that reads semantic group mapping and routes analysis.
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, List, Tuple

# --- Pseudo Imports loading deep level execution packages ---
from egm.analysis.rb import analyze_rb_standard
from egm.analysis.xeb import analyze_xeb_and_spb_from_results


class BaseAnalyzer(ABC):
    """Abstract base class establishing input/output contracts for analyzers."""
    @abstractmethod
    def run(self, results: List[Dict[str, Any]]) -> Any:
        pass

class RBAnalyzer(BaseAnalyzer):
    """RB-specific data processor passing standard flat dictionary structures."""
    def run(self, results: List[Dict[str, Any]]) -> Any:
        return analyze_rb_standard(results)

class XEBAnalyzer(BaseAnalyzer):
    """XEB-specific processor performing structural conversion prior to analysis."""
    def run(self, results: List[Dict[str, Any]]) -> Any:
        results_by_depth = defaultdict(list)
        num_qubits = len(next(iter(results[0]["data"].keys())))
        
        # Structure transformation: Convert flat standard schema into depth-grouped tuple architecture
        for item in results:
            depth = item["metadata"]["depth"]
            ideal = item["ideal_data"]
            noisy = item["data"]
            results_by_depth[depth].append((ideal, noisy))
        
        return analyze_xeb_and_spb_from_results(
            results_by_depth=dict(results_by_depth),
            num_qubits=num_qubits,
            error_bar_mode="sem"
        )


class AnalysisFactory:
    """Unified routing factory dispatching requests logically based on protocol mapping."""
    _registry = {
        "RB": RBAnalyzer,
        "XEB": XEBAnalyzer
    }

    @classmethod
    def create(cls, protocol_name: str) -> BaseAnalyzer:
        """Instantiates the explicit calculation operator corresponding to the target protocol."""
        base_name = protocol_name.split('_')[0].upper() 
        analyzer_class = cls._registry.get(base_name)
        if not analyzer_class:
            raise ValueError(f"No analyzer found for protocol: {protocol_name}")
        return analyzer_class()

    @classmethod
    def run_batch(cls, grouped_data: Dict[Tuple[str, str, Tuple[int, ...]], List[Dict]]) -> Dict[str, Any]:
        """
        Executes analysis on batches of logically organized empirical data.
        
        Args:
            grouped_data: Dictionary mapping properties like (plan_id, protocol, qubits) to results.
            
        Returns:
            Dict mapping fully qualified descriptive task string to analytical report formats.
        """
        final_reports = {}
        for (plan_id, protocol, qubits), data_list in grouped_data.items():
            # Automatically fetch and invoke the corresponding analytical model
            analyzer = cls.create(protocol)
            report = analyzer.run(data_list)
            
            # Incorporate plan_id into the final structured key for robust tracking
            qubits_str = f"[{', '.join(map(str, qubits))}]"
            task_key = f"{plan_id}_{protocol}_qubits_{qubits_str}"
            final_reports[task_key] = report
            
        return final_reports