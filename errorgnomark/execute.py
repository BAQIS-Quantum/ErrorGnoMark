# Standard library imports
import random
import logging
import re
import time
import warnings
from requests.exceptions import RequestException, ReadTimeout  # For HTTP requests and error handling
import sys
# Third-party library imports
import numpy as np  # For numerical operations
from qiskit import QuantumCircuit, qasm2, transpile  # For quantum circuit creation and transpilation
from qiskit.circuit.library import (  # Common quantum gates
    CXGate, CZGate, HGate, IGate, RXGate, RYGate, RZGate,
    SwapGate, XGate, YGate, ZGate
)
from qiskit_aer import AerSimulator  # For quantum circuit simulation
from qiskit_aer.noise import (  # Noise modeling for simulations
    NoiseModel, QuantumError, amplitude_damping_error,
    depolarizing_error, phase_damping_error
)
from qiskit_aer.noise.errors.quantum_error import NoiseError  # For handling quantum errors


from errorgnomark.token_manager import get_token
from errorgnomark.fake_data import generate_fake_data_rbq1, generate_fake_data_rbq2  # Fake data generation
from quark import Task  # Custom task handling for ErrorGnoMark

# Suppress unnecessary warnings related to multiple results
warnings.filterwarnings(
    "ignore",
    message=r'Result object contained multiple results matching name "circuit-\d+", only first match will be returned.'
)

import random



def build_custom_noise_model():
    """
    Constructs a simplified custom noise model including depolarizing, amplitude damping, and phase damping errors
    applied to all single-qubit gates.
    """
    noise_model = NoiseModel()
    
    # Define error probabilities (adjusted for target error rates)
    p_amp_1q = 0.1   # Amplitude damping probability for 1-qubit gates
    p_phase_1q = 0.005  # Phase damping probability for 1-qubit gates
    p_identity_1q = 1.0 - p_amp_1q - p_phase_1q  # No-error probability for 1-qubit gates
    p_depol_1q = 0.01  # Depolarizing error probability for 1-qubit gates

    # Validate probabilities
    if p_identity_1q < 0:
        raise ValueError("The sum of p_amp and p_phase should be <= 1 for 1-qubit gates.")
    
    # Define single-qubit gates
    single_qubit_gates = ["h", "x", "y", "z", "rx", "ry", "rz"]

    # List of possible errors to apply
    error_types = [
        lambda: amplitude_damping_error(p_amp_1q),  # Amplitude damping
        lambda: phase_damping_error(p_phase_1q),    # Phase damping
        lambda: depolarizing_error(p_depol_1q, 1)    # Depolarizing error
    ]

    # Apply noise to 1-qubit gates (for arbitrary qubit indices)
    for gate in single_qubit_gates:
        # Randomly choose the error type
        error_type = random.choice(error_types)()  # Choose and call the error type
        
        # Add the selected error to the noise model for all qubits for the current gate
        noise_model.add_all_qubit_quantum_error(error_type, gate)
    
    return noise_model

# def map_circuit(circuit, active_qubits, active_cbits):
#     """
#     Map qubits and classical bits to qubit 0 (and cbit 0) except for two-qubit gates, 
#     which will map qubit indices [0, 1] for two-qubit gates and one qubit for others.
#     """
#     # Create a new circuit with the appropriate number of qubits and classical bits
#     new_nqubits = 2 if len(active_qubits) > 1 else 1  # For two-qubit operations, keep two qubits
#     new_ncbits = 1  # Only one classical bit for the measurement result
#     new_circuit = QuantumCircuit(new_nqubits, new_ncbits)

#     # Map active qubits: if there are two qubits, map them to 0 and 1, else map to 0
#     qubit_mapping = {}
#     if len(active_qubits) == 2:
#         qubit_mapping = {active_qubits[0]: 0, active_qubits[1]: 1}
#     else:
#         qubit_mapping = {active_qubits[0]: 0}  # Map all to qubit 0 if there's only 1 qubit

#     # Map classical bits: map all classical bits to cbit 0
#     cbit_mapping = {old: 0 for old in active_cbits}

#     # Loop through instructions and map the qubits for each operation
#     for instruction, qargs, cargs in circuit.data:
#         new_qargs = []
#         for qbit in qargs:
#             new_qargs.append(new_circuit.qubits[qubit_mapping[circuit.qubits.index(qbit)]])

#         # Classical bits mapping
#         new_cargs = [new_circuit.clbits[cbit_mapping[circuit.clbits.index(cbit)]] for cbit in cargs] if cargs else []
        
#         # Add the instruction to the new circuit
#         new_circuit.append(instruction, new_qargs, new_cargs)

#     # # Debugging: Check the new circuit structure
#     # print(f"New circuit created: {new_circuit}")

#     return new_circuit, qubit_mapping, cbit_mapping


from qiskit import QuantumCircuit

def map_circuit(circuit, active_qubits, active_cbits):
    """
    Remap qubits and classical bits in `circuit` onto a compact register.

    Mapping rules
    -------------
    1. If exactly **one** qubit is used        → map it to new qubit 0
    2. If exactly **two** qubits are used      → map them to new qubits 0 and 1
    3. If **three or more** qubits are used    → sort them ascending and map to 0…N-1
    4. If N > 30                               → raise ValueError  
       (the built-in state-vector simulator in Qiskit Aer is limited to ~30 qubits)

    All classical bits are merged and mapped to the single classical bit 0.
    """
    # -------- Input sanitisation ----------
    active_qubits = sorted(set(active_qubits))
    active_cbits  = sorted(set(active_cbits))
    n_act_q       = len(active_qubits)

    # -------- Safety checks ----------
    if n_act_q == 0:
        raise ValueError("active_qubits is empty – nothing to map.")
    if n_act_q > 30:
        raise ValueError("State-vector back-ends typically support ≤30 qubits.")

    # -------- Build qubit-mapping ----------
    if n_act_q == 1:                       # Case ①: single-qubit circuit
        qubit_mapping = {active_qubits[0]: 0}
        new_nqubits   = 1
    elif n_act_q == 2:                     # Case ②: two-qubit circuit
        qubit_mapping = {
            active_qubits[0]: 0,
            active_qubits[1]: 1
        }
        new_nqubits = 2
    else:                                  # Case ③: ≥3 qubits – map sequentially
        qubit_mapping = {q: i for i, q in enumerate(active_qubits)}
        new_nqubits   = n_act_q

    # -------- Classical bits: collapse to bit 0 ----------
    new_ncbits   = 1
    cbit_mapping = {c: 0 for c in active_cbits}

    # -------- Create the new circuit ----------
    new_circ = QuantumCircuit(new_nqubits, new_ncbits)

    # -------- Re-append each instruction with remapped bits ----------
    for inst, qargs, cargs in circuit.data:
        # Remap quantum arguments
        new_qargs = [
            new_circ.qubits[ qubit_mapping[ circuit.qubits.index(q) ] ]
            for q in qargs if circuit.qubits.index(q) in qubit_mapping
        ]
        # Remap classical arguments
        new_cargs = [
            new_circ.clbits[ cbit_mapping[ circuit.clbits.index(c) ] ]
            for c in cargs if circuit.clbits.index(c) in cbit_mapping
        ]
        new_circ.append(inst, new_qargs, new_cargs)

    return new_circ, qubit_mapping, cbit_mapping


class QuantumJobRunner:
    def __init__(self, circuits):
        """
        Initializes the Quantum Job Runner.

        Parameters:
            circuits (list): A list of QuantumCircuit objects or OpenQASM strings.
                             Each element represents a single circuit execution.
        """
        self.circuits = circuits

    def validate_token(self, token):
        """
        Validates the provided QuarkStudio token.

        Parameters:
            token (str): The QuarkStudio token to validate.

        Returns:
            bool: True if the token is valid, False otherwise.
        """
        token_pattern = re.compile(r"^[\w\-\:\{\/}]+$")
        return bool(token_pattern.match(token))

    def qiskit_to_openqasm(self, circuit):
        """
        Converts a Qiskit QuantumCircuit to OpenQASM format.

        Parameters:
            circuit (QuantumCircuit): The Qiskit quantum circuit to convert.

        Returns:
            str: The circuit in OpenQASM format.
        """
        if not isinstance(circuit, QuantumCircuit):
            raise ValueError("Provided circuit is not a Qiskit QuantumCircuit.")
        return qasm2.dumps(circuit)

    def select_best_chip(self, tmgr):
        """
        Selects the chip with the minimum queue length.

        Parameters:
            tmgr (Task): The Task manager instance for QuarkStudio.

        Returns:
            str: The name of the selected chip.
        """
        status_info = tmgr.status()
        available_chips = {chip: queue for chip, queue in status_info.items() if isinstance(queue, int)}
        if not available_chips:
            raise ValueError("No available chips found.")
        return min(available_chips, key=available_chips.get)

    def quarkstudio_run(
            self,
            compile=False,
            shots=1,
            print_progress=True,
            use_fake_data=None,
            delay_between_tasks=7,
            max_retries=5,
            elapsed_time=False
        ):
            """
            Runs quantum circuits either on real hardware or generates fake data.

            Parameters:
                compile (bool): Whether to transpile the circuit to native gate sets. Default is True.
                shots (int): Number of shots per circuit. Default is 1.
                print_progress (bool): Whether to print progress updates. Default is False.
                use_fake_data (str or None): 
                    None: Execute on real hardware.
                    'fake_dataq1': 1-qubit fake data.
                    'fake_dataq2': 2-qubit fake data.
                delay_between_tasks (int): Seconds to wait after completing a task before submitting the next one. Default is 2 seconds.
                max_retries (int): Maximum number of retries for submitting a task. Default is 3.
                elapsed_time (bool): Whether to return elapsed times along with execution results. Default is False.

            Returns:
                list or tuple:
                    - If elapsed_time=False: List of measurement count dictionaries or fake data structure.
                    - If elapsed_time=True: Tuple containing the list of measurement counts and the list of elapsed times.
            """

            if use_fake_data not in [None, 'fake_dataq1', 'fake_dataq2']:
                raise ValueError("Invalid use_fake_data value. Must be one of [None, 'fake_dataq1', 'fake_dataq2'].")

            if use_fake_data:
                if use_fake_data == 'fake_dataq1':
                    return generate_fake_data_rbq1()
                elif use_fake_data == 'fake_dataq2':
                    return generate_fake_data_rbq2()
            
            # Retrieve the token
            token = get_token()
            tmgr = Task(token)
            # backend = self.select_best_chip(tmgr)
            backend = 'Baihua'
            if print_progress:
                print(f"Selected backend: {backend}")

            task_results = []
            elapsed_times = []

            for idx, circuit in enumerate(self.circuits):
                if print_progress:
                    print(f"Running circuit {idx+1}/{len(self.circuits)}...")

                openqasm_circuit = self.qiskit_to_openqasm(circuit) if isinstance(circuit, QuantumCircuit) else circuit

                task = {
                    'chip': backend,
                    'name': 'QuantumTask',
                    'circuit': openqasm_circuit,
                    'compile': compile,
                    'correct': False
                }

                attempt = 0
                while attempt < max_retries:
                    try:
                        if print_progress:
                            print(f"Submitting task for circuit {idx+1}, attempt {attempt+1}...")
                        tid = tmgr.run(task, repeat=shots)
                        break
                    except RequestException:
                        attempt += 1
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                else:
                    task_results.append({})
                    if elapsed_time:
                        elapsed_times.append(0.0)
                    continue

                while True:
                    try:
                        time.sleep(7)
                        res = tmgr.result(tid)

                        if res and 'status' in res:
                            status = res['status'].lower()
                            if print_progress:
                                print(f"Task {tid} status: {status}")
                            if status == 'finished':
                                counts = res.get('count', {})
                                task_results.append(counts)

                                if elapsed_time:
                                    task_elapsed_time = res.get('elapsed_time', 0.0)
                                    elapsed_times.append(task_elapsed_time)
                                break
                    except (ReadTimeout, RequestException):
                        time.sleep(7)

                if delay_between_tasks > 0:
                    time.sleep(delay_between_tasks)
            
            if elapsed_time:
                return task_results, np.mean(elapsed_times)
            else:

                return task_results


    def simulation_ideal_qiskit(self, compile=True, shots=4096, print_progress=False, noise_model=True, elapsed_time=False):
        # Function to get active qubits and classical bits
        def get_active_qubits_and_cbits(circuit):
            active_qubits, active_cbits = set(), set()
            for instruction, qargs, cargs in circuit.data:
                if instruction.name != 'barrier':  # Ignore barriers
                    active_qubits.update(circuit.qubits.index(qbit) for qbit in qargs)
                if instruction.name == 'measure':
                    active_cbits.update(circuit.clbits.index(cbit) for cbit in cargs)
            total_cbits = len(circuit.clbits)
            return sorted(active_qubits), sorted(active_cbits), total_cbits

        # Function to remap counts
        def remap_counts(remapped_counts, qubit_mapping, cbit_mapping, total_cbits):
            sorted_original_cbits = sorted(cbit_mapping.keys())
            final_counts = {}
            for bitstring, count in remapped_counts.items():
                bitstring = bitstring[::-1]  # Reverse the bitstring
                extracted_bits = ''.join([
                    bitstring[cbit_mapping[cbit]] for cbit in sorted_original_cbits
                ])
                final_counts[extracted_bits] = final_counts.get(extracted_bits, 0) + count
            return final_counts

        # Build noise model
        if noise_model is True:
            noise_model = build_custom_noise_model()
        elif noise_model is False or noise_model is None:
            noise_model = None

        # Initialize simulator
        simulator = AerSimulator(noise_model=noise_model)
        counts, execution_times = [], []
        total_circuits = len(self.circuits)

        # TODO active_qubits始终只有两个，这是2bit间的操作吗
        for idx, circuit in enumerate(self.circuits):
            active_qubits, active_cbits, total_cbits = get_active_qubits_and_cbits(circuit)
            if not active_qubits:
                print(f"Warning: No active qubits in circuit {idx + 1}")
                counts.append({})
                execution_times.append(0.0)
                continue

            # If there is 1 or 2 qubits, we map the circuit
            if len(active_qubits) <= 2:
                # Prepare the circuit and map qubits and classical bits
                mapped_circuit, qubit_mapping, cbit_mapping = map_circuit(circuit, active_qubits, active_cbits)
                if compile:
                    transpiled_circuit = transpile(mapped_circuit, simulator, optimization_level=0)
                else:
                    transpiled_circuit = mapped_circuit
            else:
                # For more than 2 qubits, directly execute the circuit without mapping
                transpiled_circuit = circuit

            try:
                start_time = time.time()
                job = simulator.run(transpiled_circuit, shots=shots)
                result = job.result()

                if result is None:
                    print(f"Error: No result for circuit {idx + 1}")
                    counts.append({})
                    execution_times.append(0.0)
                    continue

                elapsed = time.time() - start_time
                counts_mapped = result.get_counts(transpiled_circuit)

                if counts_mapped is None or len(counts_mapped) == 0:
                    print(f"Warning: No counts returned for circuit {idx + 1}")
                    counts.append({})
                else:
                    remapped_counts = remap_counts(counts_mapped, qubit_mapping, cbit_mapping, total_cbits) if len(active_qubits) <= 2 else counts_mapped
                    counts.append(remapped_counts)

                execution_times.append(elapsed)

            except Exception as e:
                print(f"Error running circuit {idx + 1}: {e}")
                counts.append({})
                execution_times.append(0.0)

        return (counts, np.mean(execution_times)) if elapsed_time else counts

