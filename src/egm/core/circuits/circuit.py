# =============================================================================
# File Path: egm/core/circuits/circuit.py
# [FINAL UNIFIED VERSION — SX/SY Unified Canonical Basis + Full Compatibility]
# =============================================================================

import numpy as np
from typing import List, Tuple, Any, Dict, Optional, Callable, Union, overload

from egm.core.circuits.visualization import draw_circuit_text
from egm.core.circuits.native_gates import STANDARD_NATIVE_GATES

# =============================================================================
# [[[ CANONICAL NAMES AND ALIASES — Unified SX/SY Canonicalization ]]]
# =============================================================================
ALIASES_TO_CANONICAL = {
    'cx': 'cnot',
    'u': 'u3',
    'toffoli': 'ccnot',
    'fredkin': 'cswap',
    # √X family
    'sqrtx': 'sx', 'rx90': 'sx', 'rxm90': 'sxdg',
    # √Y family
    'sqrty': 'sy', 'sqrtydg': 'sydg', 'ry90': 'sy', 'rym90': 'sydg',
}

def get_canonical_name(name: str) -> str:
    """Return canonical gate name according to aliases."""
    n = name.lower()
    return ALIASES_TO_CANONICAL.get(n, n)

# =============================================================================
# Gate Definition
# =============================================================================
class Gate:
    """Represents a single quantum gate operation (immutable and hashable)."""
    __slots__ = ('name', 'qubits', 'params', 'is_measurement')

    def __init__(self, name: str, qubits: Tuple[int, ...],
                 params: Optional[Tuple[Any, ...]] = None,
                 is_measurement: bool = False):
        self.name: str = name
        self.qubits: Tuple[int, ...] = qubits
        self.params: Tuple[Any, ...] = params if params is not None else ()
        self.is_measurement: bool = is_measurement

    @property
    def arity(self) -> int:
        return len(self.qubits)

    def inverse(self) -> "Gate":
        """Return the inverse of this gate."""
        lower = self.name.lower()
        inverse_pairs = {
            's': 'sdg', 'sdg': 's', 't': 'tdg', 'tdg': 't',
            'sx': 'sxdg', 'sxdg': 'sx', 'sy': 'sydg', 'sydg': 'sy',
            'sqrtx': 'sxdg', 'sqrty': 'sydg',
            'rx90': 'rxm90', 'rxm90': 'rx90', 'ry90': 'rym90', 'rym90': 'ry90',
            'iswap': 'iswapdg', 'iswapdg': 'iswap'
        }
        if lower in inverse_pairs:
            return Gate(inverse_pairs[lower], self.qubits, self.params)

        # Self-inverse gates
        self_inverse = [
            'h', 'x', 'y', 'z', 'id', 'cnot', 'cz', 'swap', 'ccnot',
            'cswap', 'fredkin', 'ccz', 'ecr'
        ]
        if lower in self_inverse:
            return Gate(self.name, self.qubits, self.params)

        # Parameterized rotation inversion
        if lower in ['rx', 'ry', 'rz', 'u1']:
            inv_params = tuple(-p for p in self.params)
            return Gate(self.name, self.qubits, inv_params)
        if lower == 'u2':
            phi, lam = self.params
            return Gate('u2', self.qubits, (-lam, -phi))
        if lower in ['u3', 'u']:
            theta, phi, lam = self.params
            return Gate('u3', self.qubits, (-theta, -lam, -phi))

        if lower.endswith('dg'):
            return Gate(lower[:-2], self.qubits, self.params)

        return Gate(f"{self.name}dg", self.qubits, self.params)

    def __repr__(self) -> str:
        p = f", params={self.params}" if self.params else ""
        return f"Gate(name='{self.name}', qubits={self.qubits}{p})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Gate): return NotImplemented
        return (self.name == other.name and self.qubits == other.qubits and
                self.params == other.params and self.is_measurement == other.is_measurement)

    def __hash__(self) -> int:
        return hash((self.name, self.qubits, self.params, self.is_measurement))

# =============================================================================
# QuantumCircuit
# =============================================================================
class QuantumCircuit:
    """Feature-rich abstract quantum circuit container for any backend."""
    def __init__(self, qubits: List[int], gates: Optional[List[Gate]] = None):
        if not qubits:
            raise ValueError("QuantumCircuit must be initialized with at least one qubit.")
        self.qubits = sorted(set(qubits))
        self.gates: List[Gate] = gates[:] if gates else []
        self.num_qubits = len(self.qubits)
        self.metadata: Dict[str, Any] = {}

    def __str__(self): return f"QuantumCircuit(qubits={self.qubits}, num_gates={len(self.gates)})"
    __repr__ = __str__
    def __len__(self): return len(self.gates)

    @overload
    def __getitem__(self, i: int) -> Gate: ...
    @overload
    def __getitem__(self, s: slice) -> List[Gate]: ...
    def __getitem__(self, key: Union[int, slice]):
        return self.gates[key]

    def draw(self, style: str = "text", **kwargs):
        if style == "text":
            print(draw_circuit_text(self, **kwargs))
        else:
            raise NotImplementedError(f"Drawing style '{style}' not supported.")

    def add_gate(self, g: Gate):
        self.gates.append(g)

    def add_gates(self, gs: List[Gate]):
        self.gates.extend(gs)

    def measure_all(self):
        for q in self.qubits:
            self.add_gate(Gate("measure", (q,), (), True))

    def copy(self) -> "QuantumCircuit":
        c = QuantumCircuit(self.qubits[:], self.gates[:])
        c.metadata = self.metadata.copy()
        return c

    def __add__(self, other: "QuantumCircuit") -> "QuantumCircuit":
        if not isinstance(other, QuantumCircuit): return NotImplemented
        qs = sorted(set(self.qubits) | set(other.qubits))
        gs = self.gates + other.gates
        nc = QuantumCircuit(qs, gs)
        nc.metadata = {**other.metadata, **self.metadata}
        return nc

    def inverse(self) -> "QuantumCircuit":
        inv_gates = [g.inverse() for g in reversed(self.gates)]
        inv = QuantumCircuit(self.qubits[:], inv_gates)
        inv.metadata = self.metadata.copy()
        inv.metadata["name"] = self.metadata.get("name", "circuit") + "_dg"
        return inv

    def decompose(
            self,
            basis_gates: Union[List[str], str],
            custom_rules: Optional[Dict[str, "DecompositionRule"]] = None
    ) -> "QuantumCircuit":
        """Decompose circuit gates into the given basis."""

        # *****
        if isinstance(basis_gates, str):
            key = basis_gates.lower()
            if key in STANDARD_NATIVE_GATES:
                basis_gates = STANDARD_NATIVE_GATES[key]
            else:
                raise ValueError(
                    f"Unknown native gate set '{basis_gates}'. Available: {list(STANDARD_NATIVE_GATES.keys())}")
        # *****
        basis = {b.lower() for b in basis_gates}
        canonical_basis = {get_canonical_name(b) for b in basis}
        active_map = BASE_DECOMPOSITIONS.copy()
        if "cnot" in canonical_basis and "cz" not in canonical_basis:
            active_map.update(CNOT_BASED_DECOMPOSITIONS)
        elif "cz" in canonical_basis and "cnot" not in canonical_basis:
            active_map.update(CZ_BASED_DECOMPOSITIONS)
        if custom_rules:
            active_map.update(custom_rules)

        result: List[Gate] = []
        pending = self.gates[:]
        limit = 30 * len(pending) + 1000
        i = 0
        while pending:
            i += 1
            if i > limit:
                raise RuntimeError("Decomposition exceeded iteration limit.")
            g = pending.pop(0)
            gname, canon = g.name.lower(), get_canonical_name(g.name)
            if gname in basis or canon in canonical_basis or g.is_measurement:
                result.append(g)
            else:
                rule = active_map.get(gname)
                if rule:
                    pending = rule(*g.qubits, *g.params) + pending
                else:
                    raise ValueError(f"No decomposition for gate '{g.name}'")
        newcirc = QuantumCircuit(self.qubits[:], result)
        newcirc.metadata = self.metadata.copy()
        return newcirc

# =============================================================================
# Decomposition Rules
# =============================================================================
DecompositionRule = Callable[..., List[Gate]]

CNOT_BASED_DECOMPOSITIONS = {
    "cz": lambda c, t: [Gate("h", (t,)), Gate("cnot", (c, t)), Gate("h", (t,))],
}
CZ_BASED_DECOMPOSITIONS = {
    "cnot": lambda c, t: [Gate("h", (t,)), Gate("cz", (c, t)), Gate("h", (t,))],
}

BASE_DECOMPOSITIONS: Dict[str, DecompositionRule] = {
    "swap": lambda a, b: [Gate("cnot", (a, b)), Gate("cnot", (b, a)), Gate("cnot", (a, b))],
    "iswap": lambda a, b: [Gate("s", (a,)), Gate("s", (b,)), Gate("h", (a,)),
                           Gate("cnot", (a,b)), Gate("cnot", (b,a)), Gate("h", (b,))],
    "ecr": lambda a,b:[Gate("s",(a,)),Gate("sx",(a,)),Gate("cnot",(a,b)),Gate("x",(b,))],
    "ccnot": lambda c1,c2,t:[Gate("h",(t,)),Gate("cnot",(c2,t)),Gate("tdg",(t,)),
                             Gate("cnot",(c1,t)),Gate("t",(t,)),Gate("cnot",(c2,t)),
                             Gate("tdg",(t,)),Gate("cnot",(c1,t)),Gate("t",(c2,)),
                             Gate("t",(t,)),Gate("h",(t,)),Gate("cnot",(c1,c2)),
                             Gate("t",(c1,)),Gate("tdg",(c2,)),Gate("cnot",(c1,c2))],
    "ccz": lambda c1,c2,t:[Gate("h",(t,)),Gate("ccnot",(c1,c2,t)),Gate("h",(t,))],
    "cswap": lambda c,t1,t2:[Gate("cnot",(t2,t1)),Gate("ccnot",(c,t1,t2)),Gate("cnot",(t2,t1))],
    "fredkin": lambda c,t1,t2: BASE_DECOMPOSITIONS["cswap"](c,t1,t2),

    # 缺少基础 Pauli 门（X, Y, Z）的分解规则
    "x": lambda q: [Gate("rx", (q,), (np.pi,))],
    "y": lambda q: [Gate("ry", (q,), (np.pi,))],
    "z": lambda q: [Gate("rz", (q,), (np.pi,))],
    "id": lambda q: [],

    "u3": lambda q,th,ph,la:[Gate("rz",(q,),(la,)),Gate("ry",(q,),(th,)),Gate("rz",(q,),(ph,))],
    "u": lambda q,th,ph,la: BASE_DECOMPOSITIONS["u3"](q,th,ph,la),
    "u2": lambda q,ph,la: BASE_DECOMPOSITIONS["u3"](q,np.pi/2,ph,la),
    "u1": lambda q,la:[Gate("rz",(q,),(la,))],

    "rx": lambda q,th:[Gate("h",(q,)),Gate("rz",(q,),(th,)),Gate("h",(q,))],
    "ry": lambda q,th:[Gate("sx",(q,)),Gate("rz",(q,),(th,)),Gate("sxdg",(q,))],

    "s": lambda q:[Gate("rz",(q,),(np.pi/2,))],
    "sdg": lambda q:[Gate("rz",(q,),(-np.pi/2,))],
    "t": lambda q:[Gate("rz",(q,),(np.pi/4,))],
    "tdg": lambda q:[Gate("rz",(q,),(-np.pi/4,))],
    "h": lambda q:[Gate("sx",(q,)),Gate("rz",(q,),(np.pi/2,)),Gate("sx",(q,))],

    # --- Canonical SX/SY Primitives ---
    # "sx": lambda q:[Gate("sx",(q,))],       # This caused the recursion error
    # "sxdg": lambda q:[Gate("sxdg",(q,))],   # This caused the recursion error
    "sx": lambda q: [Gate("rx", (q,), (np.pi / 2,))],
    "sxdg": lambda q: [Gate("rx", (q,), (-np.pi / 2,))],
    "sy": lambda q:[Gate("sx",(q,)),Gate("s",(q,))],
    "sydg": lambda q:[Gate("sdg",(q,)),Gate("sx",(q,))],
}

# =============================================================================
# Gate Matrix Definitions
# =============================================================================
GATE_MATRIX_MAP: Dict[str, np.ndarray] = {
    "id": np.eye(2, dtype=complex),
    "x": np.array([[0,1],[1,0]],complex),
    "y": np.array([[0,-1j],[1j,0]],complex),
    "z": np.array([[1,0],[0,-1]],complex),
    "s": np.array([[1,0],[0,1j]],complex),
    "sdg": np.array([[1,0],[0,-1j]],complex),
    "sx": np.array([[0.5+0.5j,0.5-0.5j],[0.5-0.5j,0.5+0.5j]],complex),
    "sxdg": np.array([[0.5-0.5j,0.5+0.5j],[0.5+0.5j,0.5-0.5j]],complex),
    "sy": np.array([[0.5+0.5j,0.5-0.5j],[-0.5-0.5j,0.5+0.5j]],complex),
    "sydg": np.array([[0.5-0.5j,-0.5-0.5j],[0.5+0.5j,0.5-0.5j]],complex),
    "h": np.array([[1,1],[1,-1]],complex)/np.sqrt(2),
    "cnot": np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]],complex),
    "cz": np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,-1]],complex),
    "swap": np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]],complex),
    "iswap": np.array([[1,0,0,0],[0,0,1j,0],[0,1j,0,0],[0,0,0,1]],complex),
    "iswapdg": np.array([[1,0,0,0],[0,0,-1j,0],[0,-1j,0,0],[0,0,0,1]],complex),
    "ccnot": np.eye(8, dtype=complex)[[0,1,2,3,4,5,7,6]],
    "cswap": np.eye(8, dtype=complex)[[0,1,2,3,4,6,5,7]],
    "ccz": np.diag([1,1,1,1,1,1,1,-1]),
}

def get_matrix(name: str) -> np.ndarray:
    n = name.lower()
    if n in GATE_MATRIX_MAP:
        return GATE_MATRIX_MAP[n]
    if n.endswith("dg") and n[:-2] in GATE_MATRIX_MAP:
        return GATE_MATRIX_MAP[n[:-2]].conj().T
    raise ValueError(f"No static matrix for '{name}'.")

def get_parameterized_matrix(g: Gate) -> np.ndarray:
    n = g.name.lower(); p = g.params
    if n == "rx":
        th = p[0]; return np.array([[np.cos(th/2), -1j*np.sin(th/2)],
                                   [-1j*np.sin(th/2), np.cos(th/2)]],complex)
    if n == "ry":
        th = p[0]; return np.array([[np.cos(th/2), -np.sin(th/2)],
                                   [np.sin(th/2), np.cos(th/2)]],complex)
    if n in ["rz","u1"]:
        ph = p[0]; return np.array([[np.exp(-1j*ph/2),0],[0,np.exp(1j*ph/2)]],complex)
    if n == "u2":
        ph,la=p;return np.array([[1,-np.exp(1j*la)],[np.exp(1j*ph),np.exp(1j*(ph+la))]],complex)/np.sqrt(2)
    if n in ["u3","u"]:
        th,ph,la=p
        return np.array([[np.cos(th/2), -np.exp(1j*la)*np.sin(th/2)],
                         [np.exp(1j*ph)*np.sin(th/2), np.exp(1j*(ph+la))*np.cos(th/2)]],complex)
    raise ValueError(f"No parameterized matrix rule for {g.name}")

def get_dagger(g: Gate) -> Gate:
    """Deprecated alias for Gate.inverse()."""
    return g.inverse()