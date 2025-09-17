# File Path: errorgnomark/backends/decoherence_backend.py
# MODIFIED to be more robust by ignoring case and non-essential gates.

import numpy as np
from typing import List, Dict, Union

from .base_backend import BaseBackend
from ..circuits.circuit import QuantumCircuit

class DecoherenceBackend(BaseBackend):
    """
    A specialized simulator that only models T1 and T2 decoherence effects.
    It does not simulate gate errors.
    """
    def __init__(self, t1: float, t2: float):
        # Convert microseconds from demo to seconds for calculation
        self.t1 = t1 * 1e-6
        self.t2 = t2 * 1e-6
        self.name = "DecoherenceBackend"
        print(f"DecoherenceBackend: Internal T1 set to {self.t1}s, T2 to {self.t2}s.")

    def _simulate_t1(self, delay: float, shots: int) -> Dict[str, int]:
        """Simulates decay from |1> to |0>. P(|1>) = exp(-delay / T1)."""
        # A T1 experiment starts in |1> (after an X gate). We measure the probability of it *staying* in |1>.
        prob_1 = np.exp(-delay / self.t1)
        prob_0 = 1 - prob_1
        
        # Ensure counts sum to total shots
        counts_1 = int(np.round(prob_1 * shots))
        counts_0 = shots - counts_1
        return {'0': counts_0, '1': counts_1}

    def _simulate_t2(self, delay: float, shots: int) -> Dict[str, int]:
        """Simulates decay of superposition. P(|0>) = 0.5 * (1 + exp(-delay / T2))."""
        # A T2 experiment starts in |+> (after H) and ends with another H.
        # The probability of measuring |0> is proportional to the coherence left.
        prob_0 = 0.5 * (1 + np.exp(-delay / self.t2))
        prob_1 = 1 - prob_0
        
        # Ensure counts sum to total shots
        counts_0 = int(np.round(prob_0 * shots))
        counts_1 = shots - counts_0
        return {'0': counts_0, '1': counts_1}

    def run(self, circuit: QuantumCircuit, shots: int) -> Dict[str, int]:
        """
        Runs a single decoherence experiment circuit.
        This backend is highly specialized and expects T1/T2-like circuits.
        """
        # --- FIX 1: Make all gate name comparisons case-insensitive ---
        # We convert all gate names to uppercase for consistent matching.
        all_gate_names = [gate.name.upper() for gate in circuit.gates]

        # --- FIX 2: Make sequence matching robust by ignoring measurement gates ---
        # We filter out 'MEASURE' to get the core operational sequence.
        core_gate_names = [name for name in all_gate_names if name != 'MEASURE']
        
        delay_gates = [gate for gate in circuit.gates if gate.name.upper() == 'DELAY']

        if not delay_gates:
            # This check is now case-insensitive.
            raise ValueError("DecoherenceBackend requires at least one DELAY gate in the circuit.")
        
        # The `delay` parameter is passed as a float in a list, e.g., [5e-6]
        # We sum all delays in the circuit.
        total_delay = sum(gate.params[0] for gate in delay_gates)

        # Define the expected core sequences
        is_t1 = (core_gate_names == ['X', 'DELAY'])
        is_t2_echo = (core_gate_names == ['H', 'DELAY', 'X', 'DELAY', 'H'])
        # Add T2 Ramsey for completeness, though not used in the current demo
        is_t2_ramsey = (core_gate_names == ['H', 'DELAY', 'H']) or (core_gate_names == ['H', 'DELAY', 'RZ', 'H'])

        if is_t1:
            result = self._simulate_t1(total_delay, shots)
        elif is_t2_echo or is_t2_ramsey:
            result = self._simulate_t2(total_delay, shots)
        else:
            raise NotImplementedError(
                f"The DecoherenceBackend does not support the core circuit structure: {core_gate_names}. "
                "It is specialized for T1 (['X', 'DELAY']), T2 Ramsey (e.g., ['H', 'DELAY', 'H']), "
                "and T2 Echo (['H', 'DELAY', 'X', 'DELAY', 'H']) experiments."
            )
            
        return result