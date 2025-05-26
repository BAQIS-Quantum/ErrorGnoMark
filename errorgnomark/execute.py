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


def map_circuit(circuit: QuantumCircuit,
                active_qubits=None,
                active_cbits=None):
    """
    Remap `circuit` onto a compact register, with special treatment for barrier.

    - If active_qubits is None or empty, auto-detect all qubits used in any instruction.
    - 1 qubit → map to [0]
      2 qubits → map to [0,1]
      ≥3 qubits → map sorted list to [0..N-1]
      >30 qubits → ValueError
    - All classical bits collapse to cbit 0.
    - barrier instructions are reissued only on the subset of mapped qubits.
    """
    # --- auto-detect if needed ---
    if not active_qubits:
        uq = set()
        for inst, qargs, _ in circuit.data:
            uq.update(circuit.qubits.index(q) for q in qargs)
        active_qubits = sorted(uq)
    if not active_cbits:
        uc = set()
        for inst, _, cargs in circuit.data:
            uc.update(circuit.clbits.index(c) for c in cargs)
        active_cbits = sorted(uc)

    # --- checks ---
    n_q = len(active_qubits)
    if n_q == 0:
        raise ValueError("No quantum operations to map.")
    if n_q > 30:
        raise ValueError("State-vector simulators typically support ≤30 qubits.")

    # --- build qubit map ---
    if n_q == 1:
        qmap = {active_qubits[0]: 0}
        new_nq = 1
    elif n_q == 2:
        qmap = {active_qubits[0]: 0, active_qubits[1]: 1}
        new_nq = 2
    else:
        qmap = {q: i for i, q in enumerate(active_qubits)}
        new_nq = n_q

    # --- classical bits collapse to 0 ---
    cmap = {c: 0 for c in active_cbits}
    new_nc = 1

    # --- new circuit ---
    new_circ = QuantumCircuit(new_nq, new_nc)

    # --- remap instructions ---
    for inst, qargs, cargs in circuit.data:
        # original indices
        q_idx = [circuit.qubits.index(q) for q in qargs]
        c_idx = [circuit.clbits.index(c) for c in cargs]

        # remapped lists (skip unmapped)
        new_qargs = [new_circ.qubits[qmap[i]] for i in q_idx if i in qmap]
        new_cargs = [new_circ.clbits[cmap[i]] for i in c_idx if i in cmap]

        if inst.name == "barrier":
            # only issue barrier on the mapped subset (if any)
            if new_qargs:
                new_circ.barrier(*new_qargs)
            # skip append
            continue

        # for non-barrier: fail-fast if any arg unmapped
        if set(q_idx) - set(qmap):
            raise ValueError(f"{inst.name} needs qubits {q_idx}, but only {list(qmap)} are mapped.")
        if set(c_idx) - set(cmap):
            raise ValueError(f"{inst.name} needs cbits {c_idx}, but only {list(cmap)} are mapped.")

        # append the instruction unchanged
        new_circ.append(inst, new_qargs, new_cargs)

    return new_circ, qmap, cmap


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

