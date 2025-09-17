# # errorgnomark/circuits/circuit_operations.py

# """
# We place this code in circuits/circuit_operations.py to follow the Separation of Concerns principle: separating the "building blocks" from the "assembly instructions".

# circuit.py: Defines the core blocks (the Gate and QuantumCircuit data structures).
# circuit_operations.py: Provides the instructions (functions like t1_circuit) that use those blocks to build specific, complete experiments.
# This separation makes the code cleaner, more reusable, and easier to maintain.
# """

# # errorgnomark/circuits/circuit_operations.py

# from typing import List
# from .circuit import QuantumCircuit

# def t1_circuit(qubit: int, delay: float) -> QuantumCircuit:
#     """
#     Creates a circuit to measure T1 relaxation.
#     Sequence: X -> Wait(delay) -> Measure
#     """
#     circuit = QuantumCircuit(1)
#     circuit.add_gate('X', qubit)
#     circuit.add_gate('I', qubit, duration=delay) # Identity gate represents the delay
#     circuit.add_gate('M', qubit) # Measurement
#     return circuit

# def pauli_twirling_circuit(qubit: int, gate_name: str, pauli_in: str, pauli_out: str) -> QuantumCircuit:
#     """
#     Creates a circuit for Pauli twirling.
#     Sequence: P_in -> Gate -> P_out -> Measure
#     """
#     circuit = QuantumCircuit(1)
#     if pauli_in != 'I':
#         circuit.add_gate(pauli_in, qubit)
    
#     circuit.add_gate(gate_name, qubit)

#     if pauli_out != 'I':
#         circuit.add_gate(pauli_out, qubit)
    
#     circuit.add_gate('M', qubit)
#     return circuit

# # --- NEWLY ADDED FUNCTIONS START HERE ---

# def t2_ramsey_circuit(qubit: int, delay: float, detuning: float) -> QuantumCircuit:
#     """
#     Creates a circuit to measure T2* (Ramsey experiment).
#     Sequence: H -> Wait(delay) with Z-rotation -> H -> Measure
#     """
#     circuit = QuantumCircuit(1)
#     circuit.add_gate('H', qubit)
#     # The delay is represented by an Identity gate with a duration
#     circuit.add_gate('I', qubit, duration=delay)
#     # We add a Z-rotation to simulate a frequency detuning during the delay
#     if detuning != 0.0:
#         # The angle of rotation is the detuning frequency multiplied by the delay time
#         angle = detuning * delay
#         circuit.add_gate('RZ', qubit, angle=angle)
#     circuit.add_gate('H', qubit)
#     circuit.add_gate('M', qubit)
#     return circuit

# def t2_echo_circuit(qubit: int, delay: float) -> QuantumCircuit:
#     """
#     Creates a circuit to measure T2 (Spin Echo experiment).
#     Sequence: H -> Wait(delay/2) -> X -> Wait(delay/2) -> H -> Measure
#     """
#     circuit = QuantumCircuit(1)
#     half_delay = delay / 2.0
#     circuit.add_gate('H', qubit)
#     circuit.add_gate('I', qubit, duration=half_delay)
#     circuit.add_gate('X', qubit) # The refocusing pulse
#     circuit.add_gate('I', qubit, duration=half_delay)
#     circuit.add_gate('H', qubit)
#     circuit.add_gate('M', qubit)
#     return circuit

# # --- NEWLY ADDED FUNCTIONS END HERE ---

# File Path: errorgnomark/circuits/circuit_operations.py
# MODIFIED to be compatible with the "golden" circuit.py

"""
This file provides functions that use the core blocks from circuit.py 
(Gate, QuantumCircuit) to build specific, complete experimental circuits.
"""

from typing import List
# We import the "golden" classes we must conform to.
from .circuit import QuantumCircuit, Gate


def t1_circuit(qubit: int, delay_us: float) -> QuantumCircuit:
    """
    Generates a T1 experiment circuit.
    Sequence: X - Delay - Measure

    Args:
        qubit: The target qubit.
        delay_us: The delay time in MICROSECONDS.

    Returns:
        A QuantumCircuit object for the T1 experiment.
    """
    # Convert delay from microseconds to seconds for the backend
    delay_s = delay_us * 1e-6

    circuit = QuantumCircuit(qubits=[qubit])
    circuit.add_gate(Gate('X', (qubit,)))
    # The parameter should be the float value directly
    circuit.add_gate(Gate('DELAY', (qubit,), params=[delay_s]))
    circuit.add_gate(Gate('MEASURE', (qubit,)))
    return circuit

def pauli_twirling_circuit(qubit: int, gate_name: str, pauli_in: str, pauli_out: str) -> QuantumCircuit:
    """
    Creates a circuit for Pauli twirling.
    Sequence: P_in -> Gate -> P_out -> Measure
    """
    circuit = QuantumCircuit(qubits=[qubit])
    if pauli_in.lower() != 'id':
        circuit.add_gate(Gate(pauli_in, (qubit,)))
    
    circuit.add_gate(Gate(gate_name, (qubit,)))

    if pauli_out.lower() != 'id':
        circuit.add_gate(Gate(pauli_out, (qubit,)))
    
    circuit.add_gate(Gate('measure', (qubit,)))
    return circuit

def t2_ramsey_circuit(qubit: int, delay: float, detuning: float) -> QuantumCircuit:
    """
    Creates a circuit to measure T2* (Ramsey experiment).
    Sequence: H -> Wait(delay) with Z-rotation -> H -> Measure
    """
    circuit = QuantumCircuit(qubits=[qubit])
    circuit.add_gate(Gate('h', (qubit,)))
    circuit.add_gate(Gate('delay', (qubit,), params=[delay]))
    
    # The concept of detuning is simulated by a Z rotation.
    if detuning != 0.0:
        angle = detuning * delay
        circuit.add_gate(Gate('rz', (qubit,), params=[angle]))

    circuit.add_gate(Gate('h', (qubit,)))
    circuit.add_gate(Gate('measure', (qubit,)))
    return circuit

def t2_echo_circuit(qubit: int, delay: float) -> QuantumCircuit:
    """
    Creates a circuit to measure T2 (Spin Echo experiment).
    Sequence: H -> Wait(delay/2) -> X -> Wait(delay/2) -> H -> Measure
    """
    circuit = QuantumCircuit(qubits=[qubit])
    half_delay = delay / 2.0
    
    circuit.add_gate(Gate('h', (qubit,)))
    circuit.add_gate(Gate('delay', (qubit,), params=[half_delay]))
    circuit.add_gate(Gate('x', (qubit,))) # The refocusing pulse
    circuit.add_gate(Gate('delay', (qubit,), params=[half_delay]))
    circuit.add_gate(Gate('h', (qubit,)))
    circuit.add_gate(Gate('measure', (qubit,)))
    return circuit