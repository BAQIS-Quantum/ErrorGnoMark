# Standard library imports
import random  # For generating random numbers

# Third-party imports
import numpy as np  # For numerical operations
from qiskit import QuantumCircuit, transpile  # For creating and transpiling quantum circuits
from qiskit.circuit.library import CZGate, RXGate, RYGate, RZGate,CXGate  # For specific quantum gates
from qiskit.circuit import Gate  # For general gate operations
from qiskit.quantum_info import Operator, random_unitary  # For quantum information utilities


class CliffordGateSet:
    """
    Generates random 1-qubit and 2-qubit Clifford gates based on the backend and compile settings.
    """

    def __init__(self, backend, compile=False):
        """
        Initializes the Clifford gate set generator.

        Parameters:
            backend (str): The backend ('quarkstudio', 'pyquafu', etc.).
            compile (bool): Whether to compile the Clifford gates to the backend's basis gates. Default is False.
        """
        self.backend = backend
        self.compile = compile

    def random_1qubit_clifford(self, qubit_indices):
        """
        Generates random 1-qubit Clifford gates applied to specified qubits.

        Parameters:
            qubit_indices (list): List of qubit indices to apply the gate to.

        Returns:
            QuantumCircuit: The generated Clifford gates as a QuantumCircuit.
        """
        sequences = [
            [],  # I
            ['S'],  # S
            ['S', 'S'],  # S^2 = Z
            ['S', 'S', 'S'],  # S^3 = S†
            ['H'],  # H
            ['H', 'S'],  # HS
            ['H', 'S', 'S'],  # HS^2
            ['H', 'S', 'S', 'S'],  # HS^3 = HS†
            ['S', 'H'],  # SH
            ['S', 'H', 'S'],  # SHS
            ['S', 'H', 'S', 'S'],  # SHS^2
            ['S', 'H', 'S', 'S', 'S'],  # SHS^3 = SHS†
            ['S', 'S', 'H'],  # S^2 H
            ['S', 'S', 'H', 'S'],  # S^2 HS
            ['S', 'S', 'H', 'S', 'S'],  # S^2 HS^2
            ['S', 'S', 'H', 'S', 'S', 'S'],  # S^2 HS^3 = S^2 HS†
            ['S', 'S', 'S', 'H'],  # S^3 H = S† H
            ['S', 'S', 'S', 'H', 'S'],  # S† HS
            ['S', 'S', 'S', 'H', 'S', 'S'],  # S† HS^2
            ['S', 'S', 'S', 'H', 'S', 'S', 'S'],  # S† HS^3 = S† HS†
            ['H', 'S', 'H'],  # HSH
            ['H', 'S', 'H', 'S'],  # HSHS
            ['H', 'S', 'H', 'S', 'S'],  # HSHS^2
            ['H', 'S', 'H', 'S', 'S', 'S'],  # HSHS†
        ]

        qc = QuantumCircuit(max(qubit_indices)+1)
        for i in qubit_indices:
            sequence = random.choice(sequences)
            for gate in sequence:
                if gate == 'H':
                    qc.h(i)
                elif gate == 'S':
                    qc.s(i)
                elif gate == 'S†':
                    qc.sdg(i)
        return qc

    def random_2qubit_clifford(self, qubit_pair):
        """
        Generates a random 2-qubit Clifford gate applied to a specified qubit pair.

        Parameters:
            qubit_pair (tuple): A tuple of two qubit indices to apply the 2-qubit gate to (e.g., (0, 1)).

        Returns:
            QuantumCircuit: The generated 2-qubit Clifford gate as a QuantumCircuit.
        """
        if not qubit_pair or len(qubit_pair) != 2:
            raise ValueError("qubit_pair must be a tuple of two qubit indices.")

        # Define 2-qubit Clifford operations (combinations of 1-qubit Clifford gates and CZ gates)
        qc = QuantumCircuit(max(qubit_pair) + 1)

        # Apply random 1-qubit Clifford gates to each qubit in the pair
        qc = qc.compose(self.random_1qubit_clifford(qubit_pair))
        # qc.compose(self.random_1qubit_clifford([qubit_pair[1]]))

        # Apply a CZ gate
        qc.cz(qubit_pair[0], qubit_pair[1])

        # Apply another layer of random 1-qubit Clifford gates to each qubit in the pair
        qc = qc.compose(self.random_1qubit_clifford(qubit_pair))
        # qc.compose(self.random_1qubit_clifford([qubit_pair[1]]), qubits=[qubit_pair[1]], inplace=True)

        return qc

    def random_single_gate_clifford(self, qubit_indices):
        """
        Generates a random single-gate Clifford operation (H, S, S†) applied to specified qubits.

        Parameters:
            qubit_indices (list): List of qubit indices to apply the gate to.

        Returns:
            QuantumCircuit: The generated Clifford gates as a QuantumCircuit.
        """
        qc = QuantumCircuit(max(qubit_indices)+1)
        for i in qubit_indices:
            single_gates = ['H', 'S', 'S†']
            gate = random.choice(single_gates)
            if gate == 'H':
                qc.h(i)
            elif gate == 'S':
                qc.s(i)
            elif gate == 'S†':
                qc.sdg(i)
        return qc

    def random_pauli(self, qubit_indices):
        """
        Generates random 1-qubit Pauli gates (I, X, Y, Z) applied to specified qubits.

        Parameters:
            qubit_indices (list): List of qubit indices to apply the Pauli gates to.

        Returns:
            QuantumCircuit: The generated Pauli gates as a QuantumCircuit.
        """
        qc = QuantumCircuit(max(qubit_indices)+1)
        paulis = ['X', 'Y', 'Z']
        for i in qubit_indices:
            pauli = random.choice(paulis)
            if pauli == 'X':
                qc.x(i)
            elif pauli == 'Y':
                qc.y(i)
            elif pauli == 'Z':
                qc.z(i)
            # 'I' is the identity gate; no need to append anything
        return qc



# Define possible rotation angles (in radians)
ROTATION_ANGLES = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75]

# Define available single-qubit rotation axes
SINGLE_QUBIT_GATES = ['rx', 'ry', 'rz']

# Define the two-qubit gate (CZGate) instance
CZ_GATE = CZGate()

def get_random_rotation_gate():
    """
    Randomly select a single-qubit rotation gate and its rotation angle.

    Returns:
        Gate: A randomly selected rotation gate instance.
    """
    gate_type = random.choice(SINGLE_QUBIT_GATES)
    angle = random.choice(ROTATION_ANGLES)
    if gate_type == 'rx':
        gate = RXGate(angle)
    elif gate_type == 'ry':
        gate = RYGate(angle)
    elif gate_type == 'rz':
        gate = RZGate(angle)
    else:
        raise ValueError(f"Unsupported gate type: {gate_type}")
    return gate


class csbq1_circuit_generator:
    def __init__(self, rot_axis='x', rot_angle=np.pi, rep=1):
        """
        Initialize the CSB Q1 circuit generator.

        Parameters:
            rot_axis (str): Rotation axis, can be 'x', 'y', or 'z'.
            rot_angle (float): Rotation angle for the target rotation gate.
            rep (int): Number of repetitions for the target rotation gate.
        """
        if rot_axis not in ['x', 'y', 'z']:
            raise ValueError("rot_axis must be one of 'x', 'y', or 'z'.")
        self.rot_axis = rot_axis
        self.rot_angle = rot_angle
        self.rep = rep

    def csbq1_circuit(self, lc, ini_mode, qubit_indices=[0]):
        """
        Generate a CSB Q1 circuit based on the specified circuit length and initial mode.

        Parameters:
            lc (int): Circuit length (depth).
            ini_mode (str): Initial state mode, can be 'x', 'y', or 'z'.
            qubit_indices (list): List of qubit indices, can be of arbitrary length.

        Returns:
            QuantumCircuit: The generated quantum circuit.
        """
        # Ensure the number of qubits matches the length of qubit_indices
        # num_qubits = len(qubit_indices)
        qc = QuantumCircuit(qubit_indices[0]+ 1, qubit_indices[0]+ 1)

        # Prepare the initial state
        if ini_mode == 'x':
            for q in qubit_indices:
                qc.h(q)
        elif ini_mode == 'y':
            for q in qubit_indices:
                qc.h(q)
                qc.s(q)
        elif ini_mode == 'z':
            for q in qubit_indices:
                qc.x(q)
        else:
            raise ValueError("ini_mode must be one of 'x', 'y', or 'z'.")
        qc.barrier()

        # Apply the target rotation gate repeatedly
        for _ in range(lc * self.rep):
            for q in qubit_indices:
                if self.rot_axis == 'x':
                    qc.rx(self.rot_angle, q)
                elif self.rot_axis == 'y':
                    qc.ry(self.rot_angle, q)
                elif self.rot_axis == 'z':
                    qc.rz(self.rot_angle, q)
        qc.barrier()

        # Apply inverse operations to return to the computational basis
        if ini_mode == 'x':
            for q in qubit_indices:
                qc.h(q)
        elif ini_mode == 'y':
            for q in qubit_indices:
                qc.sdg(q)
                qc.h(q)
        elif ini_mode == 'z':
            for q in qubit_indices:
                qc.x(q)
        qc.barrier()

        # Measurement
        qc.measure(qubit_indices, qubit_indices)
        return qc

    def x_direction_csbcircuit_pi_over_2(self, lc, ini_mode, qubit_indices=[0]):
        """
        Generate a CSB circuit with x-direction rotation by π/2.

        Parameters:
            lc (int): Circuit length (depth).
            ini_mode (str): Initial state mode, can be 'x', 'y', or 'z'.
            qubit_indices (list): List of qubit indices.

        Returns:
            QuantumCircuit: The generated quantum circuit.
        """
        return self.csbq1_circuit(lc, ini_mode, qubit_indices)

    def generate_csbcircuit_for_gate(self, gate_name, lc, ini_mode, qubit_indices=[0]):
        """
        Generate a CSB circuit for the specified quantum gate.

        Parameters:
            gate_name (str): Name of the quantum gate, e.g., 'XGate', 'YGate', 'ZGate', 'IdGate', 'WGate', 'HGate', 'SGate'.
            lc (int): Circuit length (depth).
            ini_mode (str): Initial state mode, can be 'x', 'y', or 'z'.
            qubit_indices (list): List of qubit indices.

        Returns:
            QuantumCircuit: The generated quantum circuit.
        """
        gate_mapping = {
            'XGate': {'rot_axis': 'x', 'rot_angle': np.pi},
            'YGate': {'rot_axis': 'y', 'rot_angle': np.pi},
            'ZGate': {'rot_axis': 'z', 'rot_angle': np.pi},
            'IdGate': {'rot_axis': 'x', 'rot_angle': 0},
            'WGate': {'rot_axis': 'x', 'rot_angle': np.pi / 4},  # Assume WGate corresponds to RX(pi/4)
            'HGate': {'rot_axis': 'x', 'rot_angle': np.pi / 2},  # Assume HGate corresponds to RX(pi/2)
            'SGate': {'rot_axis': 'z', 'rot_angle': np.pi / 2}
        }

        if gate_name not in gate_mapping:
            raise ValueError(f"Unsupported gate name: {gate_name}")

        rot_axis = gate_mapping[gate_name]['rot_axis']
        rot_angle = gate_mapping[gate_name]['rot_angle']

        # Create a new instance with the corresponding rotation axis and angle
        csb_gen = csbq1_circuit_generator(rot_axis=rot_axis, rot_angle=rot_angle, rep=self.rep)
        return csb_gen.csbq1_circuit(lc, ini_mode, qubit_indices)

    # Optional: Define individual methods for each gate
    def XGate_csbcircuit(self, lc, ini_mode, qubit_indices=[0]):
        return self.generate_csbcircuit_for_gate('XGate', lc, ini_mode, qubit_indices)

    def YGate_csbcircuit(self, lc, ini_mode, qubit_indices=[0]):
        return self.generate_csbcircuit_for_gate('YGate', lc, ini_mode, qubit_indices)

    def ZGate_csbcircuit(self, lc, ini_mode, qubit_indices=[0]):
        return self.generate_csbcircuit_for_gate('ZGate', lc, ini_mode, qubit_indices)

    def IdGate_csbcircuit(self, lc, ini_mode, qubit_indices=[0]):
        return self.generate_csbcircuit_for_gate('IdGate', lc, ini_mode, qubit_indices)

    def WGate_csbcircuit(self, lc, ini_mode, qubit_indices=[0]):
        return self.generate_csbcircuit_for_gate('WGate', lc, ini_mode, qubit_indices)

    def HGate_csbcircuit(self, lc, ini_mode, qubit_indices=[0]):
        return self.generate_csbcircuit_for_gate('HGate', lc, ini_mode, qubit_indices)

    def SGate_csbcircuit(self, lc, ini_mode, qubit_indices=[0]):
        return self.generate_csbcircuit_for_gate('SGate', lc, ini_mode, qubit_indices)


class Csbq2_cz_circuit_generator:
    def __init__(self, theta=np.pi):
        self.theta = theta  # Phase parameter for the controlled-Z gate
        self.eigval_list = [1, np.exp(1j * theta), np.exp(1j * theta), 1]  # Eigenvalue list
        self.eigvec_list = [
            np.array([1, 0, 0, 0]),  # |00> eigenstate
            np.array([0, 0, 0, 1]),  # |11> eigenstate
            1 / np.sqrt(2) * np.array([0, 1, 1, 0]),  # (|01> + |10>) eigenstate
            1 / np.sqrt(2) * np.array([0, 1, -1, 0])  # (|01> - |10>) eigenstate
        ]

    def prepare_initial_state(self, qc, mode, qubit_indices=[0, 1]):
        """
        Prepare the initial state based on the specified mode.
        """
        q0, q1 = qubit_indices
        if mode == '01':
            qc.h(q0)
            qc.cx(q0, q1)
        elif mode == '02':
            qc.h(q0)
            qc.cx(q0, q1)
            qc.h(q0)
        elif mode == '03':
            qc.h(q0)
            qc.cx(q0, q1)
            qc.h(q0)
            qc.sdg(q1)
        elif mode == '12':
            qc.h(q0)
            qc.cx(q0, q1)
            qc.h(q1)
        elif mode == '13':
            qc.h(q0)
            qc.cx(q0, q1)
            qc.h(q1)
            qc.sdg(q1)
        elif mode == '23':
            qc.x(q1)
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def prepare_inverse_initial_state(self, qc, mode, qubit_indices=[0, 1]):
        """
        Apply the inverse operation of the initial state preparation.
        """
        q0, q1 = qubit_indices
        if mode == '01':
            qc.cx(q0, q1)
            qc.h(q0)
        elif mode == '02':
            qc.h(q0)
            qc.cx(q0, q1)
            qc.h(q0)
        elif mode == '03':
            qc.s(q1)
            qc.h(q0)
            qc.cx(q0, q1)
            qc.h(q0)
        elif mode == '12':
            qc.h(q1)
            qc.cx(q0, q1)
            qc.h(q0)
        elif mode == '13':
            qc.s(q1)
            qc.h(q1)
            qc.cx(q0, q1)
            qc.h(q0)
        elif mode == '23':
            qc.x(q1)
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def csbq2_cz_circuit(self, len_list, mode='01', nrep=1, qubit_indices=[0, 1]):
        """
        Generate and return a list of two-qubit CZ circuits with customizable qubit indices.
        """
        circ_list = []

        max_qubit = max(qubit_indices) + 1

        # Prepare the initial state
        qc_ini = QuantumCircuit(max_qubit, max_qubit)
        self.prepare_initial_state(qc_ini, mode, qubit_indices)
        qc_ini.barrier()

        # Define CZ gate
        cz_gate = CZGate()

        # Define the inverse preparation operation
        qc_ini_inverse = QuantumCircuit(max_qubit, max_qubit)
        self.prepare_inverse_initial_state(qc_ini_inverse, mode, qubit_indices)

        for lc in len_list:
            qc_rep = QuantumCircuit(max_qubit, max_qubit)
            for _ in range(lc * nrep):
                qc_rep.append(cz_gate, qubit_indices)

            # Combine the initial preparation circuit and repeated circuit
            qc = qc_ini.compose(qc_rep)

            # Add the inverse operation to return to the initial state
            qc = qc.compose(qc_ini_inverse)

            # Add measurement
            qc.measure(qubit_indices, qubit_indices)

            circ_list.append(qc)

        return circ_list




class Csbq2_cnot_circuit_generator:
    def __init__(self, theta=np.pi):
        self.theta = theta  # Phase parameter for the controlled-NOT gate
        self.eigval_list = [1, -1, -1, 1]  # Eigenvalue list for CNOT gate
        self.eigvec_list = [
            np.array([1, 0, 0, 0]),  # |00> eigenstate
            np.array([0, 0, 0, 1]),  # |11> eigenstate
            1 / np.sqrt(2) * np.array([0, 1, -1, 0]),  # (|01> - |10>) eigenstate
            1 / np.sqrt(2) * np.array([0, 1, 1, 0])   # (|01> + |10>) eigenstate
        ]

    def prepare_initial_state(self, qc, mode, qubit_indices=[0, 1]):
        """
        Prepare the initial state based on the specified mode.
        """
        q0, q1 = qubit_indices
        if mode == '01':
            qc.h(q0)
            qc.cx(q0, q1)
        elif mode == '02':
            qc.h(q0)
            qc.cx(q0, q1)
            qc.h(q0)
        elif mode == '03':
            qc.h(q0)
            qc.cx(q0, q1)
            qc.h(q0)
            qc.sdg(q1)
        elif mode == '12':
            qc.h(q0)
            qc.cx(q0, q1)
            qc.h(q1)
        elif mode == '13':
            qc.h(q0)
            qc.cx(q0, q1)
            qc.h(q1)
            qc.sdg(q1)
        elif mode == '23':
            qc.x(q1)
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def prepare_inverse_initial_state(self, qc, mode, qubit_indices=[0, 1]):
        """
        Apply the inverse operation of the initial state preparation.
        """
        q0, q1 = qubit_indices
        if mode == '01':
            qc.cx(q0, q1)
            qc.h(q0)
        elif mode == '02':
            qc.h(q0)
            qc.cx(q0, q1)
            qc.h(q0)
        elif mode == '03':
            qc.s(q1)
            qc.h(q0)
            qc.cx(q0, q1)
            qc.h(q0)
        elif mode == '12':
            qc.h(q1)
            qc.cx(q0, q1)
            qc.h(q0)
        elif mode == '13':
            qc.s(q1)
            qc.h(q1)
            qc.cx(q0, q1)
            qc.h(q0)
        elif mode == '23':
            qc.x(q1)
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def csbq2_cnot_circuit(self, len_list, mode='01', nrep=1, qubit_indices=[0, 1]):
        """
        Generate and return a list of two-qubit CNOT circuits with customizable qubit indices.
        """
        circ_list = []

        max_qubit = max(qubit_indices) + 1

        # Prepare the initial state
        qc_ini = QuantumCircuit(max_qubit, max_qubit)
        self.prepare_initial_state(qc_ini, mode, qubit_indices)
        qc_ini.barrier()

        # Define CNOT gate
        cnot_gate = CXGate()

        # Define the inverse preparation operation
        qc_ini_inverse = QuantumCircuit(max_qubit, max_qubit)
        self.prepare_inverse_initial_state(qc_ini_inverse, mode, qubit_indices)

        for lc in len_list:
            qc_rep = QuantumCircuit(max_qubit, max_qubit)
            for _ in range(lc * nrep):
                qc_rep.append(cnot_gate, qubit_indices)

            # Combine the initial preparation circuit and repeated circuit
            qc = qc_ini.compose(qc_rep)

            # Add the inverse operation to return to the initial state
            qc = qc.compose(qc_ini_inverse)

            # Add measurement
            qc.measure(qubit_indices, qubit_indices)

            circ_list.append(qc)

        return circ_list









def permute_qubits(num_qubits):
    """
    Generate a random permutation of qubit indices from 0 to num_qubits - 1.
    """
    rng = np.random.default_rng()
    return list(rng.permutation(num_qubits))



def apply_random_su4_layer(qc, num_qubits):
    """
    Apply a random SU4 layer to the quantum circuit for a given number of qubits.
    
    This function:
    1. Generates a random permutation of qubits.
    2. Applies a random SU4 unitary to each adjacent pair of qubits based on the permutation.

    Args:
        qc (QuantumCircuit): The quantum circuit to modify.
        num_qubits (int): The number of qubits in the circuit.

    Returns:
        QuantumCircuit: The modified quantum circuit with SU4 layers applied.
    """
    def permute_qubits(num_qubits):
        """
        Generate a random permutation of qubit indices from 0 to num_qubits - 1.
        """
        rng = np.random.default_rng()
        return list(rng.permutation(num_qubits))
    
    # Step 1: Generate a random permutation of qubits
    permuted_qubits = permute_qubits(num_qubits)
    
    # Step 2: Apply random SU4 to each adjacent pair based on the permutation
    for qubit_idx in range(0, num_qubits, 2):
        if qubit_idx < num_qubits - 1:
            # Select the pair of qubits based on the permutation
            q1 = permuted_qubits[qubit_idx]
            q2 = permuted_qubits[qubit_idx + 1]
            
            # Generate a random SU4 unitary matrix (4x4)
            su4_unitary = random_unitary(4).data  # Qiskit's random_unitary returns a Unitery object; .data gives the matrix
            
            # Apply the unitary matrix to the selected qubits
            qc.unitary(su4_unitary, [q1, q2], label='SU4')
    
    return qc


def qv_circuit_layer(qc, num_qubits):
    """
    Add a random SU4 layer to the quantum circuit.
    """
    permute_qubits(num_qubits)
    apply_random_su4_layer(qc, num_qubits)
    return qc


