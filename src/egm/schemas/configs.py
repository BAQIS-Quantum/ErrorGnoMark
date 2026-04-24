"""
configs.py

Experiment Configuration Schema (Schema Layer).

Functionality:
This module defines the structured experiment configuration schema.
It translates user intent or automated system requirements into strong-typed parameters.
It specifies "what experiment to run", rather than "how to execute it".

Logical Architecture:
- BaseRunConfig: Top-level execution details (plan_id, backend_choice, seed).
- HardwareConfig: Target hardware constraints (chip name, gate sets, noise).
- ProtocolBundle: A grouped cluster specifying the protocol type, target qubits, and depths.
- ProtocolConfig: Manages one or more ProtocolBundles and circuit generation settings.
- VisualConfig: Parameters for visualization tools.
- ConfigSchema: Aggregates all configs, offering parsing from dict and adaptive construction.
"""

from dataclasses import dataclass, field, fields
from typing import List, Dict, Any, Optional

@dataclass
class BaseRunConfig:
    """Base execution environment configuration block."""
    plan_id: str = "EGM_Plan_Default"       # Unique identifier for the experiment plan
    backend_choice: str = "QPU"             # Backend selection (e.g., "QPU" or "Simulator")
    seed: Optional[int] = None              # Random seed, default is None for true randomness

@dataclass
class HardwareConfig:
    """Hardware and physical environment configuration block."""
    chip_name: Optional[str] = "Baihua"     # Target quantum chip name
    gate_set: List[str] = field(default_factory=list)  # Supported quantum gate set
    noise_flags: bool = False               # Flag for noise simulator

@dataclass
class ProtocolBundle:
    """
    A clustered bundle grouping protocol name, qubits, and depth.
    It represents a single scheme unit, placed one level lower than plan_id or backend.
    """
    protocol: str = "RB"                    # Experiment protocol name (e.g., RB, XEB)
    qubits: List[List[int]] = field(default_factory=lambda: [[0, 1], [2, 3]]) # Target qubit pairs
    depth: List[int] = field(default_factory=lambda: [0, 4, 12, 16])          # Circuit depths

@dataclass
class ProtocolConfig:
    """
    Quantum experiment protocol control block. 
    Can receive multiple schemes simultaneously (e.g., [RB, XEB]) by holding a list of ProtocolBundles.
    """
    # Grouping protocol, qubits, and depth into a lower-level cluster (ProtocolBundle)
    bundles: List[ProtocolBundle] = field(default_factory=lambda: [ProtocolBundle()]) 
    shots: int = 1024                       # Measurement shots per circuit
    number_of_circuits: int = 1             # Number of random circuits per depth

@dataclass
class VisualConfig:
    """Visualization rendering control block."""
    plot_heatmap: bool = False              # Whether to plot heatmaps
    plot_scatter: bool = False              # Whether to plot scatter plots
    colormap: str = "viridis"               # Colormap theme

@dataclass
class ConfigSchema:
    """Top-level configuration class aggregating all sub-modules."""
    base: BaseRunConfig
    hardware: HardwareConfig
    protocol: ProtocolConfig
    visual: VisualConfig

    def __post_init__(self):
        """
        Post-initialization hook for strict validation.
        Enforces business rule: If backend is not simulator, force noise flag to False.
        """
        if self.base.backend_choice != "Simulator":
            self.hardware.noise_flags = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigSchema":
        """
        Factory method to instantiate configuration object from a dictionary.
        Leverages dataclass default values if fields are missing.
        Retains original I/O interface.
        
        Args:
            data (Dict[str, Any]): Raw user intent dictionary
            
        Returns:
            ConfigSchema: Strongly typed configuration object
        """
        def extract_kwargs(target_class: type, source_data: dict) -> dict:
            """Helper function to extract valid keys for the target dataclass."""
            kwargs = {}
            for f in fields(target_class):
                if f.name in source_data and source_data[f.name] is not None:
                    kwargs[f.name] = source_data[f.name]
            return kwargs

        # Assemble individual blocks
        base_cfg = BaseRunConfig(**extract_kwargs(BaseRunConfig, data))
        hardware_cfg = HardwareConfig(**extract_kwargs(HardwareConfig, data))
        
        # Handle ProtocolConfig and nested ProtocolBundle for backward compatibility
        protocol_kwargs = extract_kwargs(ProtocolConfig, data)
        # If explicitly passed bundles, use them
        if "bundles" in data:
            protocol_kwargs["bundles"] = [ProtocolBundle(**b) if isinstance(b, dict) else b for b in data["bundles"]]
        # If legacy format (protocol, qubits, depth in top-level), wrap them into one bundle
        elif any(k in data for k in ("protocol", "qubits", "depth")):
            bundle_kwargs = extract_kwargs(ProtocolBundle, data)
            protocol_kwargs["bundles"] = [ProtocolBundle(**bundle_kwargs)]

        protocol_cfg = ProtocolConfig(**protocol_kwargs)
        
        vis_data = data.get("visualization", {})
        visual_cfg = VisualConfig(**extract_kwargs(VisualConfig, vis_data))

        return cls(
            base=base_cfg,
            hardware=hardware_cfg,
            protocol=protocol_cfg,
            visual=visual_cfg
        )

    @classmethod
    def from_hardware_call(cls, call_name: str, plan_id: Optional[str] = None, **kwargs) -> "ConfigSchema":
        """
        Adaptive intent construction interface connecting with the Physical Performance Layer.
        
        This dynamically builds the ConfigSchema in response to a hardware state method call
        (e.g., getting gate error triggers extensive randomized benchmarking).
        
        Args:
            call_name (str): Name of the method called in hardware_state.py (e.g., 'get_gate_error')
            plan_id (Optional[str]): Globally tracked experimental identifier tying the workflow.
            kwargs: Parameters passed to the hardware call (e.g., gate='CZ', qubits=(0, 1))

        Returns:
            ConfigSchema: Adaptively generated experiment configuration
        """
        # =====================================================================
        # PSEUDO-CODE for adaptive configuration generation based on hardware call
        # =====================================================================
        #
        # 1. Initialize empty/default base and visual configs.
        # 2. Extract target parameters (like qubits, gate) from the hardware method's kwargs.
        # 3. Formulate the path to JSON template file (templates/{call_name}.json).
        # 4. IF template exists:
        #       - Read JSON template containing 'bundles' (e.g., RB and XEB definitions).
        #       - Dynamically inherit caller's target qubits and populate into the bounds.
        # 5. ELSE:
        #       - Fallback to standard base configuration.
        # 6. RETURN composite ConfigSchema.
        # =====================================================================

        assigned_plan_id = plan_id if plan_id else f"Adaptive_{call_name}"
        base_cfg = BaseRunConfig(plan_id=assigned_plan_id)
        hardware_cfg = HardwareConfig()
        visual_cfg = VisualConfig()
        
        target_qubits = kwargs.get("qubits", [[0, 1]])
        # Ensure list of lists format for qubits
        if isinstance(target_qubits, tuple):
            target_qubits = [list(target_qubits)]
        elif isinstance(target_qubits, list) and len(target_qubits) > 0 and not isinstance(target_qubits[0], list):
            target_qubits = [target_qubits]
            
        import os
        import json
        
        # Determine the directory where this script resides and locate templates folder
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        template_path = os.path.join(template_dir, f"{call_name}.json")
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                
            # Iterate through the configuration list, parse, and dynamically inherit target parameters
            for bundle in template_data.get("bundles", []):
                # Inherit parameters such as qubits or gate down from hardware call
                if bundle.get("protocol") == "Readout":
                    bundle["qubits"] = [[q] for q in target_qubits[0]] if target_qubits else [[0]]
                else:
                    bundle["qubits"] = target_qubits
            
            protocol_cfg = ProtocolConfig(
                bundles=[ProtocolBundle(**b) for b in template_data.get("bundles", [])],
                shots=template_data.get("shots", 1024),
                number_of_circuits=template_data.get("number_of_circuits", 1)
            )
        else:
            # Fallback empty config if no JSON template found
            protocol_cfg = ProtocolConfig()

        return cls(
            base=base_cfg,
            hardware=hardware_cfg,
            protocol=protocol_cfg,
            visual=visual_cfg
        )