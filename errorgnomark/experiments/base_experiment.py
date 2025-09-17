# errorgnomark/experiments/base_experiment.py
from abc import ABC

class BaseExperiment(ABC):
    """
    Abstract Base Class for all experiments.

    This class serves as a common ancestor for all experiment-related classes,
    enabling type checking and a common conceptual framework. 
    
    IMPORTANT: It does NOT enforce any specific abstract methods. This allows 
    subclasses like atomic tasks (e.g., StandardXEBInstance) and schedulers 
    (e.g., SingleQubitGateError) to define their own, more appropriate, public
    interfaces (like `run()` or `run_and_fit()`).
    """
    pass