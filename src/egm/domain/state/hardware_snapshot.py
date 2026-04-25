"""
Immutable Hardware Snapshot.

Provides a read-only view of the hardware state at a specific time.

Snapshots are consumed by compilation and optimization routines
to ensure deterministic behavior during decision making.
"""


class HardwareSnapshot:
    """
    A read-only view of a HardwareState at a specific Version.
    """

    def __init__(self, state: HardwareState):
        self._state = state

    @property
    def version(self):
        return self._state.version

    # 所有接口只读转发

"""
HardwareSnapshot
================

Concept
-------

HardwareSnapshot represents a stable, read-only observation
of a HardwareState at a specific Version.

It defines how the hardware world model is safely observed.

Snapshot does NOT participate in evolution.
It does NOT modify state.
It does NOT create new versions.

It only provides a consistent view.


Why Snapshot Exists
-------------------

Even if HardwareState is immutable,
the system itself evolves over time:

    S0 --E1--> S1 --E2--> S2 --E3--> S3

Without Snapshot, components may accidentally read
"the latest state" during long-running tasks,
leading to:

    - inconsistent reads
    - non-reproducible compilation
    - race conditions
    - drift during execution
    - debugging difficulty

Snapshot guarantees:

    A task sees exactly one Version of the world.


Philosophy
----------

State defines what the world is.
Version defines where it sits in time.
Event defines how it changed.
Snapshot defines how it is observed.


Immutability Rule
-----------------

HardwareSnapshot must be:

    - read-only
    - lightweight
    - side-effect free

It must never:

    - mutate HardwareState
    - trigger new Events
    - fetch newer versions
    - hold mutable references


Version Binding
---------------

A Snapshot is bound to exactly one Version.

    snapshot.version == state.version

It must never silently switch to a newer state.

If a newer state is required,
a new Snapshot must be explicitly created.


Concurrency Model
-----------------

Snapshot enables safe concurrent access.

Multiple components (compiler, inference,
capacity estimation, reporting) may:

    - read the same Snapshot simultaneously
    - operate without locks
    - rely on temporal consistency

Snapshot is the foundation for:

    - long-running services
    - background calibration
    - distributed scheduling


What Snapshot Is NOT
--------------------

Snapshot is NOT:

    - a deep copy of the state
    - a persistence layer
    - a serialization artifact
    - a caching mechanism

It is a semantic observation boundary.


Long-Term Stability Rule
------------------------

If an operation requires a stable view
of the hardware world across time,
it must use a Snapshot.

If an operation modifies the world model,
it must produce an Event,
leading to a new Version and a new HardwareState.


Design Intention
----------------

Snapshot formalizes observation as a first-class concept.

Without Snapshot, temporal correctness cannot be guaranteed.

With Snapshot, the system becomes:

    - reproducible
    - concurrent-safe
    - temporally coherent
    - evolution-aware
"""

