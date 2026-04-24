"""
semantics/semantic_parser.py

通用语义层解析引擎。
职责：仅负责语义的“降维展开”与“升维重组”，不再越权调度具体的 Builder 或 Analyzer。
"""

import uuid
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Fixed imports using absolute package paths for the 'egm' namespace
from egm.schemas.configs import ConfigSchema
from egm.semantics.plan_builder import TaskInstruction

class SemanticParser:
    """
    System-level semantic data processing brain.
    Provides utility methods to unpack intent and structure raw results.
    """
    
    @classmethod
    def parse_intent(cls, config: ConfigSchema) -> List[TaskInstruction]:
        """
        [Step 1] Semantic dimensional reduction:
        Flattens a singular, nested configuration structure into a sequence of atomic, 
        non-nested TaskInstructions ready for execution planning.
        
        Args:
            config (ConfigSchema): The top-level strongly-typed execution configuration.
            
        Returns:
            List[TaskInstruction]: A flat list of separated task definitions.
        """
        # Initialize the container for generated atomic instructions
        task_instructions: List[TaskInstruction] = []
        
        # =====================================================================
        # PSEUDO-CODE: Multi-dimensional Semantic Task Extraction
        # Unpack nested scheme objects (bundles) deeply down to the atomic target 
        # qubits level. This guarantees that diverse schemes (e.g., RB, XEB) 
        # are perfectly segmented per unique qubit grouping.
        # =====================================================================
        
        # Iterate over each protocol bundle defined in the protocol configuration
        for bundle in config.protocol.bundles:
            # Extract the target protocol name
            protocol_name = bundle.protocol
            
            # Finely sub-iterate: split down to the uniquely targeted qubits level
            for qubit_pair in bundle.qubits:
                # Generate a uniquely tracking ID for the atomic task
                task_id = str(uuid.uuid4())
                
                # Construct an instruction instance aggregating logical intent and hardware info
                instruction = TaskInstruction(
                    plan_id=config.base.plan_id,
                    task_id=task_id,
                    protocol=[protocol_name],       # Encapsulate as a list (e.g., [RB]) per user standard
                    qubits=qubit_pair,
                    depth=bundle.depth,             # Fetch depth dynamically from the specific scheme bundle
                    number_of_circuits=config.protocol.number_of_circuits,
                    hardware_meta={
                        "backend": config.base.backend_choice,
                        "chip": config.hardware.chip_name,
                        "shots": config.protocol.shots,
                        "gate_set": config.hardware.gate_set,
                        "noise_flags": config.hardware.noise_flags
                    }
                )
                # Append to our instruction batch
                task_instructions.append(instruction)

        return task_instructions

    @classmethod
    def group_results(cls, raw_results: List[Dict]) -> Dict[Tuple[str, str, Tuple[int, ...]], List[Dict]]:
        """
        [Step 5] Semantic dimensional promotion:
        Derives the experiment identity (plan_id), logical origin (protocol), and physical 
        origin (qubits) from raw result data, grouping them for targeted backend analytics.
        
        Args:
            raw_results (List[Dict]): A flat list of unstructured raw result dictionaries.
            
        Returns:
            Dict[Tuple[str, str, Tuple[int, ...]], List[Dict]]: Data logically grouped by 
            (plan_id, protocol_name, qubit_tuple).
        """
        # Dictionary to hold the dynamically grouped data clusters
        grouped_data = defaultdict(list)
        
        # Process each raw result item sequentially
        for item in raw_results:
            # Enforce tracking the common experiment identity passed from upper layer
            plan_id = item.get("plan_id", "Unknown_Plan")
            
            # Extract metadata payload, defaulting to an empty dict if missing
            meta = item.get("metadata", {})
            
            # Resolve the protocol signature or assign a fallback identifier
            protocol = meta.get("protocol", "Unknown_Protocol")
            
            # Resolve the involved qubits
            qubits = meta.get("qubits", [])
            # Handle possible nested mapping structures for multiplexed groupings
            if not qubits and "groups" in meta:
                qubits = [q for group in meta["groups"] for q in group]
                
            # Aggregate the underlying data point into its matching semantic cluster
            grouped_data[(plan_id, protocol, tuple(qubits))].append(item)
            
        # Return standard dictionary to freeze the grouped state
        return dict(grouped_data)