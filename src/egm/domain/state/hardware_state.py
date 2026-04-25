
# class HardwareState:
#     """
#     Versioned hardware world model.

#     This class defines the semantic contract of the current hardware belief.
#     It does NOT expose internal storage layout.
#     """

#     # ============================================================
#     # 0. Identity / Metadata
#     # ============================================================

#     def get_version(self) -> str:
#         """Return version identifier of this hardware state."""
#         ...

#     def get_timestamp(self):
#         """Return creation or calibration timestamp."""
#         ...

#     def get_summary(self) -> dict:
#         """Return high-level summary of this state."""
#         ...


#     # ============================================================
#     # 1. Structural Layer
#     # ============================================================

#     def get_qubits(self) -> list:
#         """Return list of physical qubits."""
#         ...

#     def get_coupling_graph(self):
#         """Return connectivity graph."""
#         ...

#     def get_native_gates(self) -> list:
#         """Return supported native gate set."""
#         ...

#     def supports_gate(self, gate: str, qubits: tuple) -> bool:
#         """Check if a gate is supported on given qubits."""
#         ...


#     # ============================================================
#     # 2. Physical Performance Layer
#     # ============================================================

#     def get_gate_error(self, gate: str, qubits: tuple) -> float:
#         """Return physical gate error rate."""
#         ...

#     def get_coherence_time(self, qubit: int) -> dict:
#         """Return T1, T2, etc."""
#         ...

#     def get_readout_error(self, qubit: int) -> float:
#         """Return readout error rate."""
#         ...

#     def get_leakage_rate(self, qubit: int) -> float:
#         """Return leakage probability."""
#         ...

#     def get_crosstalk(self, source: int, target: int) -> float:
#         """Return estimated crosstalk strength."""
#         ...


#     # ============================================================
#     # 3. Noise Model Semantics
#     # ============================================================

#     def get_noise_channel(self, gate: str, qubits: tuple):
#         """Return noise channel representation for a gate."""
#         ...

#     def get_noise_model_type(self) -> str:
#         """Return high-level noise model type (e.g. depolarizing)."""
#         ...

#     def is_correlated_noise(self) -> bool:
#         """Return whether correlated noise is modeled."""
#         ...

#     def is_markovian(self) -> bool:
#         """Return whether noise is assumed Markovian."""
#         ...


#     # ============================================================
#     # 4. Logical Capability Layer
#     # ============================================================

#     def estimate_logical_error(self, code: str, distance: int) -> float:
#         """Estimate logical error rate for given code and distance."""
#         ...

#     def get_threshold_estimate(self, code_family: str) -> float:
#         """Return threshold estimate for a code family."""
#         ...

#     def get_logical_error_budget(self, code: str, distance: int) -> dict:
#         """Return breakdown of logical error contributions."""
#         ...


#     # ============================================================
#     # 5. System Capacity Layer
#     # ============================================================

#     def estimate_capacity(self, target_fidelity: float) -> dict:
#         """Estimate system capacity under target fidelity."""
#         ...

#     def estimate_max_depth(self, target_fidelity: float) -> int:
#         """Estimate maximum executable circuit depth."""
#         ...

#     def get_operating_point(self) -> dict:
#         """Return recommended operating configuration."""
#         ...


#     # ============================================================
#     # Internal (Unstable) Representation
#     # ============================================================

#     @property
#     def _raw(self):
#         """
#         Return internal representation (unstable API).
#         Use with caution.
#         """
#         ...












"""
Mutable Hardware State Model.

Represents the current runtime state of the quantum device,
including calibrated fidelities, coherence parameters, and
performance indicators.

This object is updated by profiling and calibration workflows
and serves as the source of truth for snapshot generation.
"""


"""
HardwareState
==============

HardwareState represents the complete semantic model of the hardware
at a specific version in the system evolution graph.

It is NOT:

- a parameter container
- a calibration record
- a database row
- an experiment result bundle

It IS:

- the authoritative world model of the hardware
- a versioned semantic state
- the unified view used by compiler, analysis, inference, and reporting


Core Principles
---------------

1. HardwareState is immutable.
   A new Version must be created when the world changes.

2. HardwareState does not evolve itself.
   It is transformed only via Events.

   Formally:
       State_{n+1} = f(State_n, Event_n)

3. HardwareState does not store raw experimental data.
   It stores structured, inferred, and validated knowledge.

4. HardwareState is versioned.
   Each instance is associated with a Version node that defines:
       - its position in the evolution graph
       - the triggering event
       - its physical time coordinate
       - its validity window

5. HardwareState exposes semantic interfaces,
   not internal storage layout.


Semantic Coverage
-----------------

HardwareState spans five layers:

1. Structural Layer
   - qubits
   - connectivity
   - native gates

2. Physical Performance Layer
   - error rates
   - coherence times
   - readout properties
   - leakage, crosstalk

3. Noise Model Semantics
   - channel types
   - correlation assumptions
   - Markovianity

4. Logical Capability Layer
   - logical error estimation
   - thresholds
   - error budgets

5. System Capacity Layer
   - capacity estimation
   - max depth
   - operating point


Architectural Boundaries
------------------------

HardwareState does NOT:

- run experiments
- perform inference directly
- mutate itself
- manage persistence
- control execution

Those responsibilities belong to other modules.

HardwareState is the stable semantic contract of the hardware world.


Concurrency & Observation
-------------------------

HardwareState instances are safe to read concurrently.

To observe a state safely, use HardwareSnapshot.

Never expose mutable internals.


Long-Term Evolution Note
------------------------

If a change does not alter the semantic understanding of the hardware,
it should NOT create a new HardwareState.

If the world model changes in meaning,
a new Version and a new HardwareState must be created.
"""

