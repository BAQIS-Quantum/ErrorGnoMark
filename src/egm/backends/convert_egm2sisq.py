# =============================================================================
# File    : egm/core/backends/convert_egm2sisq.py
# Version : v1.0.0 - EGM-to-SISQ Conversion Backend
# =============================================================================
"""
SISQBackend — EGM-to-SISQ Circuit Conversion Backend
-----------------------------------------------------

Provides a backend that converts ErrorGnoMark (EGM) QuantumCircuit objects
into SISQ QiProgram format for execution on SISQ-compatible hardware.

Design
------
• Inherits from ``BaseBackend`` to integrate seamlessly with the EGM engine.
• The ``run()`` method converts a circuit to SISQ format and returns the
  resulting QiProgram object alongside an empty counts dictionary.
• Batch conversion is supported via ``execute()``.
• A standalone ``egm_to_sisq()`` helper function is also provided for
  lightweight, one-off usage without instantiating the backend.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Any

import numpy as np

# --- Internal Framework Imports ---
try:
    from egm.foundation.backends.base_backend import BaseBackend
    from egm.foundation.circuits.circuit import QuantumCircuit
except ImportError:
    import sys
    import os
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    )
    from egm.foundation.backends.base_backend import BaseBackend
    from egm.foundation.circuits.circuit import QuantumCircuit

# --- SISQ / pyquiet Imports ---
from pyquiet.qir.qi_prog import QiProgram
from pyquiet.qir.qvariable import PhyQubit
from pyquiet.qir.structure import Function, FuncBody, FuncCall, Module
from pyquiet.qir.qinstructions.modules_instruction.gm import *
from pyquiet.qir.qlayout.interface import QubitDeclaration

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# =============================================================================
# Gate Mapping Table:  EGM gate name  →  SISQ instruction constructor
# =============================================================================
# Centralizing the mapping makes it easy to extend and avoids long if-elif chains.

_SINGLE_QUBIT_GATE_MAP = {
    # --- Standard gates ---
    "i": I, "id": I,
    "h": H,
    "x": X, "y": Y, "z": Z,
    "s": S, "sdg": Sdag,
    "t": T, "tdg": Tdag,
    # --- Physical / √X family ---
    "sx": Sx, "sqrtx": Sx, "sqrt_x": Sx,
    "sxdg": Sxdg,
}

_PARAMETERIZED_GATE_MAP = {
    "rx": Rx, "ry": Ry, "rz": Rz,
    "u1": U1, "u2": U2, "u3": U3, "u": U3,
}

_FIXED_ROTATION_MAP = {
    "rx90":  (Rx, [np.pi / 2]),
    "rxm90": (Rx, [-np.pi / 2]),
    "ry90":  (Ry, [np.pi / 2]),
    "rym90": (Ry, [-np.pi / 2]),
    # √Y family — no native Sy in SISQ, use Ry(π/2) as equivalent
    "sy":     (Ry, [np.pi / 2]),
    "sqrty":  (Ry, [np.pi / 2]),
    "sqrt_y": (Ry, [np.pi / 2]),
}

_TWO_QUBIT_GATE_MAP = {
    "cnot": CNOT, "cx": CNOT,
    "cz": CZ,
    "swap": SWAP,
    "iswap": ISwap,
    "ecr": ECR,
}

_THREE_QUBIT_GATE_MAP = {
    "ccnot": Toffoli, "toffoli": Toffoli,
    "cswap": Fredkin, "fredkin": Fredkin,
    "ccz": CCZ,
}


# =============================================================================
# SISQBackend — Full Backend Implementation
# =============================================================================
class SISQBackend(BaseBackend):
    """
    A conversion backend that translates EGM QuantumCircuits into SISQ
    QiProgram objects.

    This backend does **not** simulate circuits.  Instead, its ``run()``
    method performs a structural conversion so that the resulting
    QiProgram can be forwarded to SISQ-compatible hardware or compilers.

    Parameters
    ----------
    file_name : str
        Default output filename embedded in the generated QiProgram.
    qubit_name_map : Optional[Dict[int, str]]
        Mapping from logical qubit indices to physical qubit names,
        e.g. ``{0: 'q5', 1: 'q6'}``.  If ``None``, defaults to
        ``q0, q1, …``.
    """

    # -----------------------------------------------------------------
    # Initialization
    # -----------------------------------------------------------------
    def __init__(
        self,
        file_name: str = "converted.sisq",
        qubit_name_map: Optional[Dict[int, str]] = None,
    ):
        super().__init__(name="SISQBackend")
        self.file_name = file_name
        self.qubit_name_map = qubit_name_map

        logger.info(
            "[SISQBackend] Initialized (v1.0.0, EGM-to-SISQ conversion)"
        )
        logger.info(f"  Default output file : {self.file_name}")
        logger.info(
            f"  Qubit name map      : "
            f"{self.qubit_name_map or 'auto (q0, q1, ...)'}"
        )

    # -----------------------------------------------------------------
    # Core Execution  (BaseBackend contract)
    # -----------------------------------------------------------------
    def run(
        self,
        circuit: QuantumCircuit,
        shots: Optional[int] = None,
    ) -> Tuple[QiProgram, None]:
        """
        Convert a single EGM QuantumCircuit into a SISQ QiProgram.

        Parameters
        ----------
        circuit : QuantumCircuit
            The EGM circuit to convert.
        shots : Optional[int]
            Ignored (retained for interface compatibility with BaseBackend).

        Returns
        -------
        Tuple[QiProgram, None]
            ``(qi_program, None)`` — the converted SISQ program and a
            placeholder for count data (not applicable for conversion).
        """
        qi_program = egm_to_sisq(
            circuit,
            file_name=self.file_name,
            qubit_name_map=self.qubit_name_map,
        )
        return qi_program, None

    # -----------------------------------------------------------------
    # Batch Execution
    # -----------------------------------------------------------------
    def execute(
        self,
        circuits: List[QuantumCircuit],
        shots: Optional[int] = None,
    ) -> List[Tuple[QiProgram, None]]:
        """
        Convert a batch of EGM circuits into SISQ QiPrograms.

        Parameters
        ----------
        circuits : List[QuantumCircuit]
            List of EGM circuits to convert.
        shots : Optional[int]
            Ignored.

        Returns
        -------
        List[Tuple[QiProgram, None]]
            A list of ``(qi_program, None)`` tuples.
        """
        return [self.run(c, shots) for c in circuits]

    # -----------------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"<SISQBackend file='{self.file_name}', "
            f"qubit_map={self.qubit_name_map or 'auto'}>"
        )


# =============================================================================
# Standalone Conversion Function
# =============================================================================
def egm_to_sisq(
    egm_circuit: QuantumCircuit,
    file_name: str = "converted.sisq",
    qubit_name_map: Optional[Dict[int, str]] = None,
) -> QiProgram:
    """
    Convert an EGM QuantumCircuit into a SISQ QiProgram (functional API).

    Parameters
    ----------
    egm_circuit : QuantumCircuit
        The source EGM circuit.
    file_name : str
        Output filename embedded in the QiProgram.
    qubit_name_map : Optional[Dict[int, str]]
        Logical-to-physical qubit name mapping.
        Defaults to ``{0: 'q0', 1: 'q1', …}`` when ``None``.

    Returns
    -------
    QiProgram
        The converted SISQ program.
    """
    # Build qubit mapping
    if qubit_name_map is not None:
        qubit_mapping = {i: qubit_name_map[i] for i in egm_circuit.qubits}
    else:
        qubit_mapping = {i: f"q{i}" for i in egm_circuit.qubits}

    # 1. Create QiProgram
    qi_program = QiProgram(file_name)

    # 2. Load module dependency
    qi_program.load_module_set(Module.gm)

    # 3. Generate .layout section
    _generate_layout_section(qi_program, egm_circuit.qubits, qubit_mapping)

    # 4. Convert gates into .code section
    _convert_gates(qi_program, egm_circuit, qubit_mapping)

    # 5. Generate .entry section
    _generate_entry_section(qi_program)

    return qi_program


# =============================================================================
# Internal Helpers
# =============================================================================
def _generate_layout_section(
    qi_program: QiProgram,
    qubits: List[int],
    qubit_mapping: Dict[int, str],
) -> None:
    """Populate the .layout section with physical qubit declarations."""
    phy_qubits = [PhyQubit(qubit_mapping[i]) for i in qubits]
    if phy_qubits:
        qubit_decl = QubitDeclaration(phy_qubits)
        qi_program.add_layout_qubit_decl(qubit_decl)


def _convert_gates(
    qi_program: QiProgram,
    egm_circuit: QuantumCircuit,
    qubit_mapping: Dict[int, str],
) -> None:
    """Translate EGM gate operations into the .code section of QiProgram."""
    func_body = FuncBody()

    # Insert reset instruction for all qubits
    phy_qubit_vars = [PhyQubit(qubit_mapping[i]) for i in egm_circuit.qubits]
    if phy_qubit_vars:
        func_body.add_instruction(FuncCall("reset", phy_qubit_vars, []))

    # Iterate gates: collect measurements, convert all others
    measured_qubits: List[int] = []
    for gate in egm_circuit.gates:
        if gate.name.lower() == "measure" or getattr(gate, "is_measurement", False):
            measured_qubits.append(gate.qubits[0])
        else:
            instruction = _gate_to_instruction(gate, qubit_mapping)
            func_body.add_instruction(instruction)

    # Append a single merged measure call at the end
    if measured_qubits:
        measure_vars = [PhyQubit(qubit_mapping[q]) for q in measured_qubits]
        func_body.add_instruction(FuncCall("measure", measure_vars, []))

    # Wrap instructions in a Function and add to QiProgram
    function = Function()
    function.init_name("quantum_circuit")
    function.init_input_args([])
    function.init_output_args([])
    for instruction in func_body.instructions:
        function.push_instr(instruction)

    qi_program.add_define_function(function)


def _gate_to_instruction(gate, qubit_mapping: Dict[int, str]):
    """
    Map a single EGM Gate object to the corresponding SISQ instruction.

    Raises
    ------
    ValueError
        If the gate type is not supported by the current mapping.
    """
    gate_name = gate.name.lower()

    # Helper: resolve physical qubit by positional index
    def q(idx: int) -> PhyQubit:
        return PhyQubit(qubit_mapping[gate.qubits[idx]])

    # --- 1. Standard single-qubit gates (no parameters) ---
    if gate_name in _SINGLE_QUBIT_GATE_MAP:
        return _SINGLE_QUBIT_GATE_MAP[gate_name](q(0))

    # --- 2. Fixed-angle rotation gates ---
    if gate_name in _FIXED_ROTATION_MAP:
        constructor, params = _FIXED_ROTATION_MAP[gate_name]
        return constructor(q(0), params)

    # --- 3. Parameterized rotation gates ---
    if gate_name in _PARAMETERIZED_GATE_MAP and gate.params:
        return _PARAMETERIZED_GATE_MAP[gate_name](q(0), list(gate.params))

    # --- 4. Two-qubit gates ---
    if gate_name in _TWO_QUBIT_GATE_MAP:
        return _TWO_QUBIT_GATE_MAP[gate_name](q(0), q(1))

    # --- 5. Three-qubit gates ---
    if gate_name in _THREE_QUBIT_GATE_MAP:
        return _THREE_QUBIT_GATE_MAP[gate_name](q(0), q(1), q(2))

    raise ValueError(f"Unsupported gate type: '{gate.name}'")


def _generate_entry_section(qi_program: QiProgram) -> None:
    """Populate the .entry section with the main function call."""
    qi_program.add_entry_instruction(FuncCall("quantum_circuit", [], []))


# =============================================================================
# Backward-Compatible Wrapper (Deprecated)
# =============================================================================
class EGMToSISQConverter:
    """
    [Deprecated] Legacy class wrapper.

    Please use ``egm_to_sisq()`` or ``SISQBackend`` instead.
    """

    def convert(
        self,
        egm_circuit: QuantumCircuit,
        file_name: str = "converted.sisq",
        qubit_name_map: Optional[Dict[int, str]] = None,
    ) -> QiProgram:
        import warnings
        warnings.warn(
            "EGMToSISQConverter is deprecated. "
            "Use egm_to_sisq() or SISQBackend instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return egm_to_sisq(egm_circuit, file_name, qubit_name_map)