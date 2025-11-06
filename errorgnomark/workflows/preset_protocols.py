# errorgnomark/workflows/preset_protocols.py

"""
Preset, runnable workflows for common characterization and benchmarking tasks.

This module provides concrete implementations of the BaseWorkflow. Each class
here represents a ready-to-use experimental sequence, such as "run standard RB
on all single qubits."
"""

# -------------------------------------------------------------------
# 1. Standard Library Imports
# -------------------------------------------------------------------
import logging
from typing import Any, Callable, Dict, Optional

# Optional import for progress bar
try:
    from tqdm import tqdm
    _TQDM_AVAILABLE = True
except ImportError:
    _TQDM_AVAILABLE = False
    def tqdm(iterator, *args, **kwargs): return iterator

# -------------------------------------------------------------------
# 2. Internal Framework Imports
# -------------------------------------------------------------------
from errorgnomark.api import run_standard_rb
from errorgnomark.engine.executor import QuantumEngine
from errorgnomark.workflows.base import BaseWorkflow
from errorgnomark.workflows.parameter_strategies import (
    BaseParameterStrategy,
    SingleQubitSweep,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# ==============================================================================
# Concrete Workflow for Standard RB Sweep
# ==============================================================================

class StandardRBSweepWorkflow(BaseWorkflow):
    """
    A workflow to run Standard Randomized Benchmarking across multiple qubits
    as defined by a parameter strategy.
    """
    def __init__(
        self,
        strategy: BaseParameterStrategy,
        shots: int,
        api_function: Callable = run_standard_rb,
        **experiment_kwargs: Any
    ):
        """
        Initializes the RB sweep workflow.

        Args:
            strategy: The parameter strategy to use for generating qubit targets
                      (e.g., SingleQubitSweep).
            shots: The number of shots to use for each RB experiment.
            api_function: The function from the `api` module to call.
                          Defaults to `run_standard_rb`.
            **experiment_kwargs: Fixed keyword arguments to pass to every call
                                 of the api_function (e.g., `depths`, `seed`).
        """
        super().__init__(
            name="Standard RB Sweep",
            description=f"Runs {api_function.__name__} using a {strategy.__class__.__name__} strategy."
        )
        self.strategy = strategy
        self.shots = shots
        self.api_function = api_function
        self.experiment_kwargs = experiment_kwargs

    def execute(self, engine: QuantumEngine, show_progress: bool = True) -> Dict[str, Any]:
        """
        Executes the RB sweep.

        It gets device properties from the engine, generates parameter sets
        from the strategy, and runs the RB experiment for each set.

        Args:
            engine: The QuantumEngine to run on.
            show_progress: If True, display a progress bar.

        Returns:
            A dictionary where keys are string identifiers for the run
            (e.g., 'qubits_[0]') and values are the RB result dictionaries.
        """
        logging.info(f"--- Starting Workflow: {self.name} ---")
        logging.info(f"Description: {self.description}")
        
        num_qubits = engine.get_num_qubits()
        topology = engine.get_topology()
        
        # Generate the list of parameter sets to iterate over
        param_sets = list(self.strategy.generate(num_qubits, topology))
        
        if not param_sets:
            logging.warning("Parameter strategy generated no tasks. Workflow finished with no action.")
            return {}

        all_results = {}
        
        iterator = tqdm(param_sets, desc="Running RB Sweep", disable=not (show_progress and _TQDM_AVAILABLE))

        for param_set in iterator:
            # Create a unique key for this run's results.
            # e.g., for {'qubits': [0]}, key becomes 'qubits_[0]'
            key = "_".join(f"{k}_{v}" for k, v in sorted(param_set.items()))
            
            # Combine fixed kwargs with the current swept parameters
            current_kwargs = self.experiment_kwargs.copy()
            current_kwargs.update(param_set)
            
            logging.info(f"\nExecuting task for parameters: {param_set}")
            
            # Run the experiment for the current parameter set
            result = self.api_function(
                engine=engine,
                shots=self.shots,
                plot=False,  # Plotting is typically handled post-workflow
                **current_kwargs
            )
            
            all_results[key] = result

        logging.info(f"--- Workflow '{self.name}' Finished ---")
        return all_results

# ==============================================================================
# Example Usage
# ==============================================================================
if __name__ == '__main__':
    # This block demonstrates how a user would use the workflow.
    # It serves as a simple integration test and usage example.

    from errorgnomark.backends.ideal_backend import IdealQuantumEngine

    # 1. Configure the backend engine
    # Using an ideal engine with some phenomenological noise for demonstration
    ideal_engine = IdealQuantumEngine(num_qubits=3, default_error_rate=0.001)

    # 2. Define the parameter strategy
    # We want to run 1-qubit RB on all available qubits.
    sweep_strategy = SingleQubitSweep()

    # 3. Instantiate the workflow
    # We pass the strategy, shots, and any fixed parameters for the RB runs.
    rb_workflow = StandardRBSweepWorkflow(
        strategy=sweep_strategy,
        shots=512,
        depths=[1, 10, 20, 50, 80], # Fixed depths for all runs
        circuits_per_depth=15,
        seed=42
    )

    # 4. Execute the workflow
    workflow_results = rb_workflow.execute(ideal_engine)

    # 5. Process and print the results
    print("\n\n--- Workflow Results Summary ---")
    for run_key, result in workflow_results.items():
        if result and result.get("fit_successful"):
            epc = result.get('epc', float('nan'))
            print(f"Run '{run_key}': Fit successful, EPC = {epc:.4e}")
        else:
            print(f"Run '{run_key}': Fit failed or no result.")
    
    # Example output:
    # --- Workflow Results Summary ---
    # Run 'qubits_[0]': Fit successful, EPC = 7.5123e-04
    # Run 'qubits_[1]': Fit successful, EPC = 7.4988e-04
    # Run 'qubits_[2]': Fit successful, EPC = 7.5050e-04