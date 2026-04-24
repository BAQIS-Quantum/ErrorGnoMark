"""
suites/config_factory.py

Script Functionality:
This script contains generic utilities for creating configuration schemas.
It defines standard generation paths (direct explicit intent and adaptive hardware intents)
so it can be shared across multiple executable applications and demo scripts.

Logical Architecture:
- ConfigFactory: A generic class/module containing generation routines to parse 
                 dictionaries or trigger physical metric adaptive payloads.
"""

from typing import Dict, Any, Optional
from egm.schemas.configs import ConfigSchema

def generate_configuration(
    mode: str = "direct",
    plan_id: Optional[str] = None,
    intent_dict: Optional[Dict[str, Any]] = None,
    call_name: Optional[str] = None,
    hardware_kwargs: Optional[Dict[str, Any]] = None
) -> ConfigSchema:
    """
    Demonstrates two standard pathways to dynamically compile the configuration schema based
    on externally injected explicit arguments.
    
    Args:
        mode (str): Generation selection. Supports 'direct' for manual payload objects or 
                    'adaptive' for templates triggered by upper hardware state calls.
        plan_id (Optional[str]): Globally tracked experimental identifier tying the workflow.
        intent_dict (Optional[Dict]): The explicit raw semantic dictionary mapped by user.
        call_name (Optional[str]): Original hardware execution metric being queried.
        hardware_kwargs (Optional[Dict]): Physical attributes passed down the stack (e.g. gate type).
        
    Returns:
        ConfigSchema: The strongly typed config ready to govern the experiment sequence.
    """
    if mode == "direct":
        # =====================================================================
        # PSEUDO-CODE: Direct Definition Pathway
        # Injects the validated dictionary to instantiate the robust core definitions.
        # =====================================================================
        if intent_dict is None:
            raise ValueError("Parameter 'intent_dict' must be provided in 'direct' mode.")
            
        if plan_id:
            intent_dict["plan_id"] = plan_id
            
        print(">>> [ConfigFactory] Parsing explicitly provided user intent into Config...")
        return ConfigSchema.from_dict(intent_dict)
        
    elif mode == "adaptive":
        # =====================================================================
        # PSEUDO-CODE: Adaptive Generation Pathway
        # Triggers dynamic template loading (like get_gate_error.json) from hardware layer.
        # =====================================================================
        if call_name is None:
            raise ValueError("Parameter 'call_name' must be provided in 'adaptive' mode.")
            
        hw_kwargs = hardware_kwargs or {}
        print(f">>> [ConfigFactory] Generating adaptive Config via {call_name} trigger...")
        return ConfigSchema.from_hardware_call(
            call_name=call_name, 
            plan_id=plan_id,
            **hw_kwargs
        )
    else:
        raise ValueError(f"Unknown generation mode requested: {mode}")
