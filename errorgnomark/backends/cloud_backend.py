# errorgnomark/backends/cloud_backend.py

import abc
from typing import List, Tuple, Dict, Any, Optional, TYPE_CHECKING

# Import the base class it needs to extend from the same package
from .base_backend import BaseBackend

# Use a forward reference for type hinting to avoid circular imports.
# This is crucial if your QuantumCircuit class needs to import things from backends.
if TYPE_CHECKING:
    from ..circuits.circuit import QuantumCircuit

class CloudBackend(BaseBackend, abc.ABC):
    """
    An abstract base class for backends that connect to cloud-based quantum providers.

    This class provides a template for the common workflow of interacting with a
    quantum cloud service, using the "Template Method" design pattern. The `run`
    method defines the skeleton of the algorithm, and subclasses must implement
    the specific steps.

    Any specific cloud provider backend (e.g., for Quafu, IBM, Google, IonQ) must
    inherit from this class and implement all its abstract methods.
    """

    def __init__(self, device_name: Optional[str], **credentials: Any):
        """
        Initializes the CloudBackend. This constructor starts the connection process.

        Args:
            device_name (Optional[str]): The specific name of the quantum device to use.
                If None or a special value like "auto", the subclass is expected
                to perform automatic selection of the best available device.
            **credentials (Any): A dictionary of credentials required for authentication,
                e.g., `token="...", api_key="..."`. This flexible approach supports
                various authentication schemes.
        """
        super().__init__()
        # Subclasses MUST override this attribute for clear identification.
        self.provider_name: str = "Abstract Cloud Provider" 
        self.device_name = device_name
        self.credentials = credentials
        
        # This holds the live connection object (e.g., a provider or device object from the SDK).
        # It is initialized by the abstract method below. The name 'handle' is used to
        # indicate it's an opaque object from an external library.
        print(f"  - [CloudBackend] Initializing connection for provider '{self.provider_name}'...")
        self.device_handle: Any = self._authenticate_and_get_device_handle()
        
        if self.device_handle:
            print(f"  - [CloudBackend] Connection successful.")
        else:
            # The abstract method should raise an error on failure, but this is a safeguard.
            raise ConnectionError(f"Authentication and device handle retrieval failed for {self.provider_name}.")

    # --------------------------------------------------------------------------
    #  Abstract methods that subclasses MUST implement
    # --------------------------------------------------------------------------

    @abc.abstractmethod
    def _authenticate_and_get_device_handle(self) -> Any:
        """
        Handles provider-specific authentication and returns a device handle.

        This method should use `self.credentials` and `self.device_name` to:
        1. Authenticate with the cloud service.
        2. If `self.device_name` is not specified, select a default or "best" device.
        3. Return a handle or object that will be used for subsequent API calls
           (e.g., the main provider object, a specific backend object, etc.).

        This method is called exactly once during `__init__`.

        Returns:
            An object representing the connected device/provider from the SDK.
            The type is `Any` as it is specific to each provider.
        """
        pass

    @abc.abstractmethod
    def _translate_circuits(self, circuits: List['QuantumCircuit']) -> Any:
        """
        Translates internal QuantumCircuit objects into the provider-specific format.

        Args:
            circuits (List['QuantumCircuit']): A list of circuit objects from this framework.

        Returns:
            Circuits in the format required by the provider's SDK (e.g., a list of
            Qiskit circuits, Cirq circuits, or OpenQASM strings).
        """
        pass

    @abc.abstractmethod
    def _run_job_and_get_results(self, provider_circuits: Any, shots: int) -> Any:
        """
        Submits the translated circuits, waits for execution, and retrieves the raw results.

        This method should encapsulate the entire job lifecycle for the provider:
        - Submitting the `provider_circuits`.
        - Polling for job completion if the process is asynchronous.
        - Handling provider-specific configurations like batching, retries, or timeouts.

        Args:
            provider_circuits (Any): The circuits in the provider-specific format.
            shots (int): The number of measurement shots for the experiment.

        Returns:
            A raw results object from the provider's SDK.
        """
        pass

    @abc.abstractmethod
    def _parse_results(self, job_results: Any, num_circuits: int) -> List[Tuple[Dict[str, float], Dict[str, int]]]:
        """
        Parses the provider's raw results object into the framework's standard format.

        Args:
            job_results (Any): The raw results object from `_run_job_and_get_results`.
            num_circuits (int): The number of circuits that were run, which can help in
                                parsing batched results.

        Returns:
            A list of tuples, where each tuple is `(probabilities, counts)`.
            - probabilities: A dictionary mapping measurement outcomes (str) to their
                             estimated probabilities (float).
            - counts: A dictionary mapping measurement outcomes (str) to their
                      observed shot counts (int).
        """
        pass

    # --------------------------------------------------------------------------
    #  Concrete "Template Method" - Subclasses should NOT override this
    # --------------------------------------------------------------------------

    def run(self, circuits: List['QuantumCircuit'], shots: int) -> List[Tuple[Dict[str, float], Dict[str, int]]]:
        """
        Executes the full workflow for running circuits on the cloud backend.
        
        This method orchestrates the calls to the abstract methods in the correct
        sequence. It acts as the "template" for the execution algorithm.
        """
        print(f"  - [CloudBackend] Starting run of {len(circuits)} circuits on '{self.provider_name}'...")
        
        # Step 1: Translate circuits
        print(f"  - [CloudBackend] Translating circuits...")
        provider_circuits = self._translate_circuits(circuits)
        
        # Step 2: Submit job and wait for raw results
        print(f"  - [CloudBackend] Submitting job for {shots} shots...")
        job_results = self._run_job_and_get_results(provider_circuits, shots)
        print("  - [CloudBackend] Job complete, raw results received.")
        
        # Step 3: Parse raw results into standard format
        print("  - [CloudBackend] Parsing results...")
        parsed_data = self._parse_results(job_results, len(circuits))
        
        print("  - [CloudBackend] Run finished successfully.")
        return parsed_data