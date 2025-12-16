# File Path: errorgnomark/circuits/circuit.py
# [DEFINITIVE FINAL VERSION - Enhanced with Immutability and Flexibility]

import numpy as np
from typing import List, Tuple, Any, Dict, Optional, Callable, Union, overload

from egm.core.circuits.visualization import draw_circuit_text

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# [[[ CANONICAL NAMES AND ALIASES ]]]
# This map defines the "one true name" for gates that have multiple aliases.
# The key is the alias, the value is the canonical name.
ALIASES_TO_CANONICAL = {
    'cx': 'cnot',
    'u': 'u3',
    'toffoli': 'ccnot',
    'fredkin': 'cswap',
    'sqrtx': 'sx',
}

def get_canonical_name(name: str) -> str:
    """Returns the canonical name for a given gate name."""
    name_lower = name.lower()
    return ALIASES_TO_CANONICAL.get(name_lower, name_lower)
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


class Gate:
    """
    Represents a single quantum gate operation as a class.

    This object is designed to be immutable and hashable, allowing it to be used
    in sets or as dictionary keys for advanced circuit transformations.
    """
    # __slots__ can slightly improve memory usage and access speed.
    __slots__ = ('name', 'qubits', 'params', 'is_measurement')

    def __init__(self, name: str, qubits: Tuple[int, ...], params: Optional[Tuple[Any, ...]] = None, is_measurement: bool = False):
        """
        Initializes an immutable Gate object.

        Args:
            name (str): The name of the gate (e.g., 'h', 'cnot').
            qubits (Tuple[int, ...]): A tuple of qubit indices the gate acts on.
            params (Optional[Tuple[Any, ...]]): A tuple of parameters (e.g., angles).
                                                Must be a tuple to ensure hashability.
            is_measurement (bool): True if this operation is a measurement.
        """
        self.name: str = name
        self.qubits: Tuple[int, ...] = qubits
        self.params: Tuple[Any, ...] = params if params is not None else ()
        self.is_measurement: bool = is_measurement

    @property
    def arity(self) -> int:
        return len(self.qubits)

    def inverse(self) -> 'Gate':
        """
        Returns a new Gate object that is the inverse of this gate.
        Does not modify the original gate.
        """
        lower_name = self.name.lower()
        inverse_pairs = {
            's': 'sdg', 'sdg': 's', 't': 'tdg', 'tdg': 't',
            'rx90': 'rxm90', 'rxm90': 'rx90', 'ry90': 'rym90', 'rym90': 'ry90',
            'sqrtx': 'sxdg', 'sx': 'sxdg'
        }
        if lower_name in inverse_pairs:
            return Gate(name=inverse_pairs[lower_name], qubits=self.qubits, params=self.params)
        
        self_inverse_gates = [
            'h', 'x', 'y', 'z', 'id', 'cnot', 'cz', 'swap',
            'ccnot', 'toffoli', 'cswap', 'fredkin', 'ccz', 'ecr'
        ]
        if lower_name in self_inverse_gates:
            return Gate(name=self.name, qubits=self.qubits, params=self.params)
        
        if lower_name in ['rx', 'ry', 'rz', 'u1']:
            # Parameters must be tuples, so we create a new one.
            inv_params = tuple(-p for p in self.params)
            return Gate(name=self.name, qubits=self.qubits, params=inv_params)
        if lower_name == 'u2':
            phi, lam = self.params
            return Gate(name='u2', qubits=self.qubits, params=(-lam, -phi))
        if lower_name == 'u3' or lower_name == 'u':
            theta, phi, lam = self.params
            return Gate(name='u3', qubits=self.qubits, params=(-theta, -lam, -phi))

        if lower_name.endswith('dg'):
            base_name = self.name[:-2]
            return Gate(name=base_name, qubits=self.qubits, params=self.params)
            
        return Gate(name=f"{self.name}dg", qubits=self.qubits, params=self.params)

    def __repr__(self) -> str:
        param_str = f", params={self.params}" if self.params else ""
        return f"Gate(name='{self.name}', qubits={self.qubits}{param_str})"

    def __eq__(self, other: object) -> bool:
        """Checks for equality between two Gate objects."""
        if not isinstance(other, Gate):
            return NotImplemented
        return (self.name == other.name and
                self.qubits == other.qubits and
                self.params == other.params and
                self.is_measurement == other.is_measurement)

    def __hash__(self) -> int:
        """Makes the Gate object hashable."""
        return hash((self.name, self.qubits, self.params, self.is_measurement))


class QuantumCircuit:
    """A feature-rich, framework-agnostic data structure for a quantum circuit."""
    def __init__(self, qubits: List[int], gates: Optional[List[Gate]] = None):
        if not qubits:
            raise ValueError("QuantumCircuit must be initialized with a list of qubit indices.")
        self.qubits = sorted(list(set(qubits)))
        self.gates: List[Gate] = gates if gates is not None else []
        self.num_qubits = len(self.qubits)
        self.metadata: Dict[str, Any] = {}

    def __str__(self) -> str:
        return f"QuantumCircuit(qubits={self.qubits}, num_gates={len(self.gates)})"

    def __repr__(self) -> str:
        return f"QuantumCircuit(qubits={self.qubits}, num_gates={len(self.gates)})"
    
    def __len__(self) -> int:
        """Returns the number of gates in the circuit."""
        return len(self.gates)

    @overload
    def __getitem__(self, item: int) -> Gate: ...
    @overload
    def __getitem__(self, item: slice) -> List[Gate]: ...
    def __getitem__(self, item: Union[int, slice]) -> Union[Gate, List[Gate]]:
        """Allows accessing gates by index or slice."""
        return self.gates[item]

    def draw(self, style: str = 'text', **kwargs):
        if style == 'text':
            print(draw_circuit_text(self, **kwargs))
        else:
            raise NotImplementedError(f"Drawing style '{style}' is not supported.")

    def add_gate(self, gate: Gate):
        self.gates.append(gate)

    def add_gates(self, gates: List[Gate]):
        self.gates.extend(gates)

    def measure_all(self):
        for q_index in self.qubits:
            # Ensure params is a tuple for the new Gate
            self.add_gate(Gate('measure', (q_index,), params=(), is_measurement=True))

    def copy(self) -> 'QuantumCircuit':
        """Creates a new QuantumCircuit with a copy of the gates and metadata."""
        new_gates = self.gates[:] # Creates a shallow copy of the list
        new_qubits = self.qubits[:]
        new_circuit = QuantumCircuit(qubits=new_qubits, gates=new_gates)
        new_circuit.metadata = self.metadata.copy()
        return new_circuit

    def __add__(self, other: 'QuantumCircuit') -> 'QuantumCircuit':
        """Combines two circuits, returning a new one."""
        if not isinstance(other, QuantumCircuit):
            return NotImplemented
        combined_qubits: List[int] = sorted(list(set(self.qubits) | set(other.qubits)))
        combined_gates: List[Gate] = self.gates + other.gates
        new_circuit = QuantumCircuit(qubits=combined_qubits, gates=combined_gates)
        # Metadata from 'self' takes precedence in case of key collision
        new_circuit.metadata = {**other.metadata, **self.metadata}
        return new_circuit

    def inverse(self) -> 'QuantumCircuit':
        """
        Returns a new circuit that is the inverse of this circuit.

        The new circuit contains the inverse of each gate in reverse order.
        The original circuit is not modified.
        """
        # Create a new list of inverted gates in reverse order
        reversed_inverted_gates = [gate.inverse() for gate in reversed(self.gates)]
        
        # Create a new circuit object with the new gate list
        inv_circuit = QuantumCircuit(qubits=self.qubits[:], gates=reversed_inverted_gates)
        inv_circuit.metadata = self.metadata.copy()
        inv_circuit.metadata['name'] = self.metadata.get('name', 'circuit') + '_dg'
        
        return inv_circuit

    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    # [[[ ENHANCED: DYNAMIC DECOMPOSITION ENGINE ]]]
    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    def decompose(
        self, 
        basis_gates: List[str], 
        custom_rules: Optional[Dict[str, 'DecompositionRule']] = None
    ) -> 'QuantumCircuit':
        """
        Decomposes the circuit into a new circuit using a specified basis.

        This method returns a *new* QuantumCircuit object and does not modify
        the original. It uses a dynamic strategy based on the provided basis
        and can be extended with custom decomposition rules.

        Args:
            basis_gates (List[str]): A list of gate names that are considered native.
            custom_rules (Optional[Dict[str, DecompositionRule]]): A dictionary mapping
                gate names to decomposition functions. These rules take precedence
                over the built-in rules.

        Returns:
            QuantumCircuit: A new circuit containing only gates from the basis set.
        """
        basis_set = set(g.lower() for g in basis_gates)
        canonical_basis_set = {get_canonical_name(g) for g in basis_set}
        
        # --- Dynamic Strategy Selection ---
        # 1. Start with the universal base decompositions.
        active_decomposition_map = BASE_DECOMPOSITIONS.copy()

        # 2. Check the basis set to decide on a 2-qubit gate strategy.
        is_cnot_native = 'cnot' in canonical_basis_set
        is_cz_native = 'cz' in canonical_basis_set

        if is_cnot_native and not is_cz_native:
            active_decomposition_map.update(CNOT_BASED_DECOMPOSITIONS)
        elif is_cz_native and not is_cnot_native:
            active_decomposition_map.update(CZ_BASED_DECOMPOSITIONS)
        
        # 3. Apply custom rules, which have the highest priority.
        if custom_rules:
            active_decomposition_map.update(custom_rules)
        
        final_gates: List[Gate] = []
        # Process a copy of the gate list, leaving the original circuit untouched.
        gates_to_process = self.gates[:]
        
        max_iterations = 30 * len(self.gates) + 1000 
        iterations = 0

        while gates_to_process:
            iterations += 1
            if iterations > max_iterations:
                problem_gate = gates_to_process[0]
                raise RuntimeError(
                    f"Decomposition exceeded max iterations, likely due to an infinite loop. "
                    f"Problematic gate: {problem_gate.name}."
                )

            gate = gates_to_process.pop(0)
            gate_name_lower = gate.name.lower()
            canonical_gate_name = get_canonical_name(gate_name_lower)

            if gate_name_lower in basis_set or canonical_gate_name in canonical_basis_set or gate.is_measurement:
                final_gates.append(gate)
            else:
                decomp_func = active_decomposition_map.get(gate_name_lower)
                if decomp_func:
                    # Unpack qubits and params tuples into the function call
                    decomposed_gates = decomp_func(*gate.qubits, *gate.params)
                    # Prepend the new gates to the list to continue decomposition
                    gates_to_process = decomposed_gates + gates_to_process
                else:
                    raise ValueError(
                        f"Cannot decompose gate '{gate.name}'. It is not in the basis "
                        f"set {basis_set}, its canonical form '{canonical_gate_name}' is not represented in the "
                        f"canonical basis {canonical_basis_set}, and no decomposition rule was found for the current strategy."
                    )
        
        # Create and return the new, fully decomposed circuit.
        decomposed_circuit = QuantumCircuit(qubits=self.qubits[:], gates=final_gates)
        decomposed_circuit.metadata = self.metadata.copy()
        
        return decomposed_circuit

DecompositionRule = Callable[..., List[Gate]]

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# [[[ STRATEGY-BASED DECOMPOSITION MAPS ]]]
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv

# --- Strategy 1: CNOT-based Decompositions ---
CNOT_BASED_DECOMPOSITIONS: Dict[str, DecompositionRule] = {
    'cz': lambda c, t: [Gate('h', (t,)), Gate('cnot', (c, t)), Gate('h', (t,))]
}

# --- Strategy 2: CZ-based Decompositions ---
CZ_BASED_DECOMPOSITIONS: Dict[str, DecompositionRule] = {
    'cnot': lambda c, t: [Gate('h', (t,)), Gate('cz', (c, t)), Gate('h', (t,))]
}

# --- Base Decompositions (Universal / Default to CNOT) ---
BASE_DECOMPOSITIONS: Dict[str, DecompositionRule] = {
    # --- Level 5: Complex Gates ---
    'swap': lambda a, b: [Gate('cnot', (a, b)), Gate('cnot', (b, a)), Gate('cnot', (a, b))],
    'iswap': lambda a, b: [Gate('s', (a,)), Gate('s', (b,)), Gate('h', (a,)), Gate('cnot', (a,b)), Gate('cnot', (b,a)), Gate('h', (b,))],
    'ecr': lambda a, b: [Gate('s', (a,)), Gate('sx', (a,)), Gate('cnot', (a, b)), Gate('x', (b,))],
    'ccnot': lambda c1, c2, t: [
        Gate('h', (t,)), Gate('cnot', (c2, t)), Gate('tdg', (t,)),
        Gate('cnot', (c1, t)), Gate('t', (t,)), Gate('cnot', (c2, t)),
        Gate('tdg', (t,)), Gate('cnot', (c1, t)), Gate('t', (c2,)),
        Gate('t', (t,)), Gate('h', (t,)), Gate('cnot', (c1, c2)),
        Gate('t', (c1,)), Gate('tdg', (c2,)), Gate('cnot', (c1, c2))
    ],
    'toffoli': lambda c1, c2, t: BASE_DECOMPOSITIONS['ccnot'](c1, c2, t),
    'ccz': lambda c1, c2, t: [Gate('h', (t,)), Gate('ccnot', (c1, c2, t)), Gate('h', (t,))],
    'cswap': lambda c, t1, t2: [Gate('cnot', (t2, t1)), Gate('ccnot', (c, t1, t2)), Gate('cnot', (t2, t1))],
    'fredkin': lambda c, t1, t2: BASE_DECOMPOSITIONS['cswap'](c, t1, t2),

    # --- Level 4: Universal Gates & Aliases ---
    'cx': lambda c, t: [Gate('cnot', (c, t))],
    'u3': lambda q, theta, phi, lam: [
        Gate('rz', (q,), (lam,)),
        Gate('ry', (q,), (theta,)),
        Gate('rz', (q,), (phi,)),
    ],
    'u': lambda q, theta, phi, lam: BASE_DECOMPOSITIONS['u3'](q, theta, phi, lam),
    'u2': lambda q, phi, lam: BASE_DECOMPOSITIONS['u3'](q, np.pi/2, phi, lam),
    'u1': lambda q, lam: [Gate('rz', (q,), (lam,))],

    # --- Level 3: Common Single-Qubit Gates ---
    'rx': lambda q, theta: [
        Gate('h', (q,)),
        Gate('rz', (q,), (theta,)),
        Gate('h', (q,)),
    ],
    'ry': lambda q, theta: [
        Gate('sx', (q,)),
        Gate('rz', (q,), (theta,)),
        Gate('sxdg', (q,)),
    ],
    'y': lambda q: [Gate('rz', (q,), (np.pi,)), Gate('x', (q,))],
    's': lambda q: [Gate('rz', (q,), (np.pi/2,))],
    'sdg': lambda q: [Gate('rz', (q,), (-np.pi/2,))],
    't': lambda q: [Gate('rz', (q,), (np.pi/4,))],
    'tdg': lambda q: [Gate('rz', (q,), (-np.pi/4,))],
    
    # --- Level 2: Physical-like Gates ---
    'h': lambda q: [Gate('sx', (q,)), Gate('rz', (q,), (np.pi/2,)), Gate('sx', (q,))] ,
    'z': lambda q: [Gate('rz', (q,), (np.pi,))],
    'x': lambda q: [Gate('h', (q,)), Gate('z', (q,)), Gate('h', (q,))] ,
    'sqrtx': lambda q: [Gate('sx', (q,))],
    'rx90': lambda q: [Gate('sx', (q,))],
    'rxm90': lambda q: [Gate('sxdg', (q,))],
    'ry90': lambda q: [Gate('sx', (q,)), Gate('s', (q,))] ,
    'rym90': lambda q: [Gate('sdg', (q,)), Gate('sx', (q,))] ,
    'sxdg': lambda q: [Gate('rz', (q,), (-np.pi,)), Gate('sx', (q,)), Gate('rz', (q,), (-np.pi,))],
}

# --- The rest of the file remains unchanged ---
# (Matrix maps and functions are omitted for brevity but are assumed to be the same as before)
GATE_MATRIX_MAP: Dict[str, np.ndarray] = {
    'id': np.eye(2, dtype=complex), 'h': np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),
    'x': np.array([[0, 1], [1, 0]], dtype=complex), 'y': np.array([[0, -1j], [1j, 0]], dtype=complex),
    'z': np.array([[1, 0], [0, -1]], dtype=complex), 's': np.array([[1, 0], [0, 1j]], dtype=complex),
    'sdg': np.array([[1, 0], [0, -1j]], dtype=complex), 't': np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex),
    'tdg': np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex),
    'sqrtx': np.array([[0.5+0.5j, 0.5-0.5j], [0.5-0.5j, 0.5+0.5j]], dtype=complex),
    'sx': np.array([[0.5+0.5j, 0.5-0.5j], [0.5-0.5j, 0.5+0.5j]], dtype=complex),
    'sxdg': np.array([[0.5-0.5j, 0.5+0.5j], [0.5+0.5j, 0.5-0.5j]], dtype=complex),
    'rx90': np.array([[1, -1j], [-1j, 1]], dtype=complex) / np.sqrt(2),
    'rxm90': np.array([[1, 1j], [1j, 1]], dtype=complex) / np.sqrt(2),
    'ry90': np.array([[1, -1], [1, 1]], dtype=complex) / np.sqrt(2),
    'rym90': np.array([[1, 1], [-1, 1]], dtype=complex) / np.sqrt(2),
    'cnot': np.array([[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]], dtype=complex),
    'cx': np.array([[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]], dtype=complex),
    'cz': np.array([[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,-1]], dtype=complex),
    'swap': np.array([[1,0,0,0], [0,0,1,0], [0,1,0,0], [0,0,0,1]], dtype=complex),
    'ccnot': np.eye(8, dtype=complex)[[0,1,2,3,4,5,7,6]],
    'toffoli': np.eye(8, dtype=complex)[[0,1,2,3,4,5,7,6]],
    'cswap': np.eye(8, dtype=complex)[[0,1,2,3,4,6,5,7]],
    'fredkin': np.eye(8, dtype=complex)[[0,1,2,3,4,6,5,7]],
}

def get_matrix(gate_name: str) -> np.ndarray:
    lookup_name = gate_name.lower()
    matrix = GATE_MATRIX_MAP.get(lookup_name)
    if matrix is not None:
        return matrix
    if lookup_name.endswith('dg'):
        base_name = lookup_name[:-2]
        base_matrix = GATE_MATRIX_MAP.get(base_name)
        if base_matrix is not None:
            return base_matrix.conj().T
    raise ValueError(f"Matrix for gate '{gate_name}' not found in GATE_MATRIX_MAP. "
                     "For parameterized gates, use get_parameterized_matrix() or ensure they are decomposed.")

def get_parameterized_matrix(gate: Gate) -> np.ndarray:
    name = gate.name.lower()
    params = gate.params
    if name == 'rx':
        theta = params[0]
        return np.array([[np.cos(theta/2), -1j*np.sin(theta/2)],
                         [-1j*np.sin(theta/2), np.cos(theta/2)]], dtype=complex)
    if name == 'ry':
        theta = params[0]
        return np.array([[np.cos(theta/2), -np.sin(theta/2)],
                         [np.sin(theta/2), np.cos(theta/2)]], dtype=complex)
    if name == 'rz' or name == 'u1':
        phi = params[0]
        return np.array([[np.exp(-1j*phi/2), 0],
                         [0, np.exp(1j*phi/2)]], dtype=complex)
    if name == 'u2':
        phi, lam = params
        return np.array([[1, -np.exp(1j*lam)],
                         [np.exp(1j*phi), np.exp(1j*(phi+lam))]], dtype=complex) / np.sqrt(2)
    if name == 'u3' or name == 'u':
        theta, phi, lam = params
        return np.array([
            [np.cos(theta/2), -np.exp(1j*lam)*np.sin(theta/2)],
            [np.exp(1j*phi)*np.sin(theta/2), np.exp(1j*(phi+lam))*np.cos(theta/2)]
        ], dtype=complex)
    raise ValueError(f"Matrix construction rule for parameterized gate '{gate.name}' not found.")

def get_dagger(gate: Gate) -> Gate:
    """[DEPRECATED] Use gate.inverse() instead."""
    return gate.inverse()

# TODO-20251118-Enhanced with Concurrent Layers & Compatibility
"""Circuits: the pygsti.objects.Circuit Python class represents a sequence
of quantum operations on qubits/qudits. Circuits are similar to Python tuples 
of circuit layers, and circuit layers are similar to tuples of gate labels. 
(A “layer” is a collection of operations that are executed concurrently.) 
Circuits can be translated to IBM’s OpenQASM language [26] and Rigetti 
Comput- ing’s Quil language [37], allowing characterization protocols 
to easily be run on widely accessible “cloud” devices [38, 39]."""