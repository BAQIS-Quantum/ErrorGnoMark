# File Path: errorgnomark/circuits/circuit.py
# [DEFINITIVE FINAL VERSION v8 - Added Clifford gate matrices]

import numpy as np
from typing import List, Tuple, Any, Dict, Optional, Callable

# This import is now safe because visualization.py no longer imports back at runtime.
from .visualization import draw_circuit_text

class Gate:
    """
    Represents a single quantum gate operation as a class.
    """
    def __init__(self, name: str, qubits: Tuple[int, ...], params: List[Any] = None, is_measurement: bool = False):
        self.name = name
        self.qubits = qubits
        self.params = params if params is not None else []
        self.is_measurement = is_measurement

    @property
    def arity(self) -> int:
        return len(self.qubits)

    def inverse(self) -> 'Gate':
        lower_name = self.name.lower()
        inverse_pairs = {
            's': 'sdg', 'sdg': 's', 't': 'tdg', 'tdg': 't',
            'rx90': 'rxm90', 'rxm90': 'rx90', 'ry90': 'rym90', 'rym90': 'ry90',
            'sqrtx': 'sqrtxdg', 'sx': 'sxdg'
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
            return Gate(name=self.name, qubits=self.qubits, params=[-p for p in self.params])
        if lower_name == 'u2':
            phi, lam = self.params
            return Gate(name='u2', qubits=self.qubits, params=[-lam, -phi])
        if lower_name == 'u3' or lower_name == 'u':
            theta, phi, lam = self.params
            return Gate(name='u3', qubits=self.qubits, params=[-theta, -lam, -phi])

        if lower_name.endswith('dg'):
            base_name = self.name[:-2]
            return Gate(name=base_name, qubits=self.qubits, params=self.params)
            
        return Gate(name=f"{self.name}dg", qubits=self.qubits, params=self.params)

    def __repr__(self) -> str:
        param_str = f", params={self.params}" if self.params else ""
        return f"Gate(name='{self.name}', qubits={self.qubits}{param_str})"


class QuantumCircuit:
    """A feature-rich, framework-agnostic data structure for a quantum circuit."""
    def __init__(self, qubits: List[int], gates: Optional[List[Gate]] = None):
        if not qubits:
            raise ValueError("QuantumCircuit must be initialized with a list of qubit indices.")
        self.qubits = sorted(list(set(qubits)))
        self.gates = gates if gates is not None else []
        self.num_qubits = len(self.qubits)

    def __str__(self) -> str:
        return f"QuantumCircuit(qubits={self.qubits}, num_gates={len(self.gates)})"

    def __repr__(self) -> str:
        return f"QuantumCircuit(qubits={self.qubits}, num_gates={len(self.gates)})"

    def draw(self, style: str = 'text', **kwargs):
        if style == 'text':
            print(draw_circuit_text(self, **kwargs))
        else:
            raise NotImplementedError(f"Drawing style '{style}' is not supported.")

    def add_gate(self, gate: Gate):
        self.gates.append(gate)

    def measure_all(self):
        for q_index in self.qubits:
            self.add_gate(Gate('measure', (q_index,), is_measurement=True))

    def copy(self) -> 'QuantumCircuit':
        new_gates = [g for g in self.gates]
        new_qubits = self.qubits[:]
        return QuantumCircuit(qubits=new_qubits, gates=new_gates)

    def __add__(self, other: 'QuantumCircuit') -> 'QuantumCircuit':
        if not isinstance(other, QuantumCircuit):
            return NotImplemented
        combined_qubits: List[int] = sorted(list(set(self.qubits) | set(other.qubits)))
        combined_gates: List[Gate] = self.gates + other.gates
        return QuantumCircuit(qubits=combined_qubits, gates=combined_gates)

    def decompose(self, basis_gates: List[str]) -> 'QuantumCircuit':
        basis_set = set(g.lower() for g in basis_gates)
        final_gates: List[Gate] = []
        gates_to_process = self.gates[:]
        
        max_iterations = 20 * len(self.gates) + 500 
        iterations = 0

        while gates_to_process:
            iterations += 1
            if iterations > max_iterations:
                problem_gate = gates_to_process[0]
                raise RuntimeError(
                    f"Decomposition exceeded max iterations, likely due to an infinite loop. "
                    f"Problematic gate: {problem_gate.name}. This can happen if a gate's decomposition "
                    f"rule produces gates that are not in the basis set {basis_set} and also lack "
                    f"their own valid, non-circular decomposition rules."
                )

            gate = gates_to_process.pop(0)
            gate_name_lower = gate.name.lower()

            if gate_name_lower in basis_set or gate.is_measurement:
                final_gates.append(gate)
            else:
                decomp_func = GATE_DECOMPOSITION_MAP.get(gate_name_lower)
                if decomp_func:
                    decomposed_gates = decomp_func(*gate.qubits, *gate.params)
                    gates_to_process = decomposed_gates + gates_to_process
                else:
                    raise ValueError(
                        f"Cannot decompose gate '{gate.name}'. It is not in the basis "
                        f"set {basis_set} and has no rule in GATE_DECOMPOSITION_MAP."
                    )
        
        return QuantumCircuit(qubits=self.qubits, gates=final_gates)

DecompositionRule = Callable[..., List[Gate]]

GATE_DECOMPOSITION_MAP: Dict[str, DecompositionRule] = {
    'u3': lambda q, theta, phi, lam: [
        Gate('rz', (q,), [lam]),
        Gate('ry', (q,), [theta]),
        Gate('rz', (q,), [phi]),
    ],
    'u': lambda q, theta, phi, lam: GATE_DECOMPOSITION_MAP['u3'](q, theta, phi, lam),
    'u2': lambda q, phi, lam: GATE_DECOMPOSITION_MAP['u3'](q, np.pi/2, phi, lam),
    'u1': lambda q, lam: [Gate('rz', (q,), [lam])],
    'ry': lambda q, theta: [
        Gate('h', (q,)),
        Gate('rx', (q,), [theta]),
        Gate('h', (q,)),
    ],
    'rx': lambda q, theta: [
        Gate('h', (q,)),
        Gate('rz', (q,), [theta]),
        Gate('h', (q,)),
    ],
    'cnot': lambda c, t: [Gate('h', (t,)), Gate('cz', (c, t)), Gate('h', (t,))],
    'cx': lambda c, t: GATE_DECOMPOSITION_MAP['cnot'](c, t),
    'cz': lambda c, t: [Gate('h', (t,)), Gate('cnot', (c, t)), Gate('h', (t,))],
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
    'toffoli': lambda c1, c2, t: GATE_DECOMPOSITION_MAP['ccnot'](c1, c2, t),
    'ccz': lambda c1, c2, t: [Gate('h', (t,)), Gate('ccnot', (c1, c2, t)), Gate('h', (t,))],
    'cswap': lambda c, t1, t2: [Gate('cnot', (t2, t1)), Gate('ccnot', (c, t1, t2)), Gate('cnot', (t2, t1))],
    'fredkin': lambda c, t1, t2: GATE_DECOMPOSITION_MAP['cswap'](c, t1, t2),
    'y': lambda q: [Gate('z', (q,)), Gate('x', (q,))],
    's': lambda q: [Gate('t', (q,)), Gate('t', (q,))],
    'sdg': lambda q: [Gate('tdg', (q,)), Gate('tdg', (q,))],
    'sx': lambda q: [Gate('s', (q,)), Gate('h', (q,)), Gate('s', (q,))],
    'sxdg': lambda q: [Gate('sx', (q,)), Gate('sx', (q,)), Gate('sx', (q,))],
    'sqrtx': lambda q: GATE_DECOMPOSITION_MAP['sx'](q),
    'rx90': lambda q: [Gate('sx', (q,))],
    'rxm90': lambda q: [Gate('sxdg', (q,))],
    'ry90': lambda q: [
        Gate('rz', (q,), [-np.pi/2]),
        Gate('sx', (q,)),
        Gate('rz', (q,), [np.pi/2])
    ],
    'rym90': lambda q: [
        Gate('rz', (q,), [np.pi/2]),
        Gate('sx', (q,)),
        Gate('rz', (q,), [-np.pi/2])
    ],
    'h': lambda q: [Gate('sx', (q,)), Gate('rz', (q,), [np.pi/2]), Gate('sx', (q,))],
    'z': lambda q: [Gate('rz', (q,), [np.pi])],
    'x': lambda q: [Gate('h', (q,)), Gate('z', (q,)), Gate('h', (q,))]
}

GATE_MATRIX_MAP: Dict[str, np.ndarray] = {
    'id': np.eye(2, dtype=complex), 'h': np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),
    'x': np.array([[0, 1], [1, 0]], dtype=complex), 'y': np.array([[0, -1j], [1j, 0]], dtype=complex),
    'z': np.array([[1, 0], [0, -1]], dtype=complex), 's': np.array([[1, 0], [0, 1j]], dtype=complex),
    'sdg': np.array([[1, 0], [0, -1j]], dtype=complex), 't': np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex),
    'tdg': np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex),
    'sqrtx': np.array([[0.5+0.5j, 0.5-0.5j], [0.5-0.5j, 0.5+0.5j]], dtype=complex),
    'sx': np.array([[0.5+0.5j, 0.5-0.5j], [0.5-0.5j, 0.5+0.5j]], dtype=complex),
    'sxdg': np.array([[0.5-0.5j, 0.5+0.5j], [0.5+0.5j, 0.5-0.5j]], dtype=complex),
    
    # <<< FIX: ADDED MISSING CLIFFORD GATE MATRICES >>>
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
    """Retrieves the matrix for a given non-parameterized gate name."""
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