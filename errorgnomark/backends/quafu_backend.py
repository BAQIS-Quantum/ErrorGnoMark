# errorgnomark/backends/quafu_backend.py
# TODO 1: Enhance network robustness. The current sequential, blocking calls to
#       `send_task` and `wait_for_result` are vulnerable to network latency and
#       connection interruptions. Future improvements should include:
#       1. Implementing a retry mechanism with exponential backoff for API requests.
#       2. Adding timeouts to network calls to prevent indefinite hanging.
#       3. Exploring asynchronous submission of all tasks first, followed by a
#          polling loop to fetch results, which would improve throughput.
# TODO 2 : Subject: Deadlock when using multiprocessing with changing qubit contexts
# Problem:

# The Python SDK causes a process deadlock when used with Python's multiprocessing module. The deadlock occurs consistently when we create child processes in a loop to submit jobs for different qubit configurations (e.g., first for qubits=[0, 1], then for qubits=[2, 3]).

# However, if we use a fixed qubit configuration for all child processes, the program runs stably without any issues.

# This indicates the root cause is the SDK's internal state management, which appears not to be fork-safe. When a child process inherits the SDK state from its parent and then tries to reconfigure it for a new set of qubits, it leads to a resource conflict and a deadlock at a low level.

# Solution / Workaround:

# We resolved this by abandoning multiprocessing and instead using the subprocess module. Each task is executed in a completely new, isolated process via a command-line call (e.g., python worker_script.py). This approach avoids inheriting any state from the parent process, thus preventing the deadlock.

# We recommend reviewing the SDK's resource handling in a fork environment to ensure it is fully fork-safe.




"""
This module provides the backend for connecting to the Quafu quantum cloud platform.
It implements the abstract CloudBackend class.
"""

import time
from typing import List, Tuple, Dict, Any, Optional, TYPE_CHECKING

# Gracefully handle the case where the 'quafu' SDK is not installed.
try:
    from quafu import User, Task
except ImportError:
    # Set to None so we can check for it later.
    User = None
    Task = None

# Import the abstract base class and framework-specific data structures
from .cloud_backend import CloudBackend
from ..circuits.to_openqasm import to_openqasm

# Use a forward reference for type hinting to avoid circular imports
if TYPE_CHECKING:
    from ..circuits.circuit import QuantumCircuit


class QuafuBackend(CloudBackend):
    """
    A backend to execute quantum circuits on the Quafu cloud platform.

    This class handles authentication, circuit translation to OpenQASM 2.0,
    job submission, and result parsing for the Quafu service.
    """

    def __init__(self, device_name: Optional[str] = "ScQ-P10", **credentials: Any):
        """
        Initializes the QuafuBackend.

        Args:
            device_name (Optional[str]): The name of the Quafu device to use.
                Defaults to "ScQ-P10". If set to None, the backend will attempt
                to automatically select an available online device.
            **credentials (Any): Must contain a 'token' key with the Quafu API token.
                Example: `QuafuBackend(token="your_api_token_here")`
        """
        if User is None or Task is None:
            raise ImportError(
                "The 'quafu' SDK is not installed. "
                "Please install it to use QuafuBackend: pip install quafu"
            )

        # Set the provider name BEFORE calling the parent constructor
        # so that its logging messages are accurate.
        self.provider_name = "Quafu"
        
        # Call the parent class's __init__ to start the connection process.
        # This will, in turn, call our implementation of _authenticate_and_get_device_handle.
        super().__init__(device_name=device_name, **credentials)

    def _authenticate_and_get_device_handle(self) -> 'User':
        """
        Authenticates with the Quafu service using an API token.

        This method retrieves the token from `self.credentials` and uses it to
        configure a Quafu `User` object, which serves as the main handle for
        all subsequent API interactions.

        Returns:
            User: An authenticated Quafu User object.

        Raises:
            ValueError: If the API token is not provided in the credentials.
        """
        print("    - [QuafuBackend] Authenticating with Quafu service...")
        
        token = self.credentials.get('token')
        if not token:
            raise ValueError("A 'token' must be provided in the credentials for QuafuBackend.")

        user = User()
        user.save_apitoken(token)
        
        print("    - [QuafuBackend] Authentication successful.")
        return user

    def _translate_circuits(self, circuits: List['QuantumCircuit']) -> List[str]:
        """
        Translates a list of internal QuantumCircuit objects to OpenQASM 2.0 strings.

        Quafu backends primarily accept OpenQASM 2.0. This method uses the dedicated
        `to_openqasm` converter for this purpose.

        Args:
            circuits (List['QuantumCircuit']): A list of circuits to be translated.

        Returns:
            List[str]: A list of OpenQASM 2.0 strings, one for each circuit.
        """
        print("    - [QuafuBackend] Translating internal circuits to OpenQASM 2.0 format...")
        try:
            # We explicitly target OpenQASM 2.0 for broad compatibility with Quafu.
            return [to_openqasm(c, measure_all=True, qasm_version=2.0) for c in circuits]
        except ValueError as e:
            print(f"ERROR: Failed to translate a circuit to OpenQASM. Reason: {e}")
            raise  # Re-raise the exception to halt the execution.

    def _run_job_and_get_results(self, provider_circuits: List[str], shots: int) -> List['Task']:
        """
        Submits circuits one by one to Quafu and waits for their results.

        Quafu's current `send_task` API is designed for single-circuit submissions.
        This method iterates through the provided QASM strings, submits each as a
        separate task, and waits for it to complete before submitting the next.

        Args:
            provider_circuits (List[str]): A list of OpenQASM 2.0 strings.
            shots (int): The number of shots for each experiment.

        Returns:
            List[Task]: A list of completed Quafu Task objects, each containing results.
        """
        user: User = self.device_handle
        
        # Handle automatic device selection if no device was specified during init
        backend_name = self.device_name
        if backend_name is None:
            print("    - [QuafuBackend] No device specified. Selecting an available online backend...")
            available_backends = user.get_available_backends()
            online_backends = [b for b in available_backends if b.status == "online"]
            if not online_backends:
                raise RuntimeError("No online Quafu backends are currently available.")
            # Pick the first available online backend as a default
            backend_name = online_backends[0].name
            print(f"    - [QuafuBackend] Automatically selected backend: '{backend_name}'")
        
        completed_tasks = []
        num_circuits = len(provider_circuits)

        for i, qasm_str in enumerate(provider_circuits):
            print(f"    - [QuafuBackend] Submitting circuit {i+1}/{num_circuits} to '{backend_name}'...")
            
            # Submit the task
            task = user.send_task(qasm=qasm_str, shots=shots, backend=backend_name)
            print(f"    - [QuafuBackend] Task '{task.task_id}' submitted. Waiting for completion...")
            
            # Wait for the result. This is a blocking call.
            result = task.wait_for_result()
            print(f"    - [QuafuBackend] Task '{task.task_id}' completed with status: {result.trans_status}")
            
            completed_tasks.append(result)

            # Be a good citizen: add a small delay between task submissions
            if i < num_circuits - 1:
                time.sleep(1)

        return completed_tasks

    def _parse_results(self, job_results: List[Any], num_circuits: int) -> List[Tuple[Dict[str, float], Dict[str, int]]]:
        """
        Parses a list of completed Quafu Task objects into the framework's standard format.

        Args:
            job_results (List[Any]): A list of raw result objects from Quafu (completed Tasks).
            num_circuits (int): The number of circuits that were run.

        Returns:
            A list of tuples, where each tuple is `(probabilities, counts)`.
        """
        parsed_data = []
        for result in job_results:
            # The Quafu result object conveniently provides both counts and probabilities
            counts = result.counts
            probabilities = result.probabilities
            parsed_data.append((probabilities, counts))
        return parsed_data