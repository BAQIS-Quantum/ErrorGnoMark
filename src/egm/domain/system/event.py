# class Event:
#     id: str
#     physical_time: datetime


# class StructuralEvent(Event):
#     pass


# class PerformanceEvent(Event):
#     pass


# class CapacityEvent(Event):
#     pass



# class QubitDisabled(StructuralEvent):
#     ...

# class ErrorRatesUpdated(PerformanceEvent):
#     ...

# class LogicalModelRefined(CapacityEvent):
#     ...

"""
Event Model
===========

Concept
-------

Event represents a semantic change to the Hardware world model.

HardwareState does NOT mutate itself.
It evolves only through Events.

    State_{n+1} = f(State_n, Event_n)

An Event describes *what changed in the world's understanding*,
not how code executed.


What Event Is NOT
-----------------

Event is NOT:

- a function call
- a calibration script
- a database record
- an experiment artifact
- a command

Those are operational concepts.

Event is a domain concept:
    A formal description of a change in hardware knowledge.


Why Strong-Typed Events
-----------------------

We intentionally avoid a generic:

    Event(type: str, payload: dict)

because that approach:

- weakens semantic guarantees
- removes structural validation
- shifts correctness to runtime
- encourages uncontrolled drift

Instead, Events are grouped by semantic layer of impact.


Current Minimal Event Hierarchy
-------------------------------

To avoid type explosion while preserving semantics,
we define three primary Event categories:

    Event (base class)
        ├── StructuralEvent
        ├── PerformanceEvent
        └── CapacityEvent


1) StructuralEvent
   ----------------
   Changes hardware structure.

   Examples:
       - Qubit disabled/enabled
       - Coupling map modification
       - Native gate set change

   These events modify the Structural Layer
   of the HardwareState.


2) PerformanceEvent
   -----------------
   Changes physical performance knowledge.

   Examples:
       - Calibration completed
       - Error rates re-inferred
       - Noise model parameters updated
       - Crosstalk re-estimated

   These events modify:
       - Physical performance layer
       - Noise semantics layer


3) CapacityEvent
   --------------
   Changes logical or system-level capability estimation.

   Examples:
       - Logical error model refined
       - Threshold re-estimated
       - Max depth recalculated
       - Compiler feedback integrated

   These events modify:
       - Logical capability layer
       - System capacity layer


Why We Do NOT Classify by Workflow
-----------------------------------

We intentionally avoid categories such as:

    - CalibrationEvent
    - CompilerEvent
    - AutomationEvent

Because those are workflow concepts,
not world-semantic concepts.

Events must be categorized by
which layer of the world model changes,
not by which tool produced them.

Workflows may evolve.
World layers remain stable.


Extensibility Strategy
----------------------

If future complexity increases, extend carefully:

Option A: Add concrete subclasses under existing categories.

    class QubitDisabled(StructuralEvent): ...
    class ErrorRatesUpdated(PerformanceEvent): ...
    class LogicalModelRefined(CapacityEvent): ...

This keeps semantics strong without exploding base categories.

Option B (advanced): Introduce intermediate layer groups
if a category becomes too large.

Do NOT:

    - Collapse back to string-based type dispatch
    - Embed large payload dictionaries
    - Allow Events to carry full state snapshots


Design Constraints
------------------

- Events must be immutable.
- Events must be lightweight.
- Events must not contain full HardwareState.
- Events should describe change, not store resulting state.
- Events must be versionable and referenceable by ID.


Relationship to Version
-----------------------

When an Event occurs:

    1) It has a physical timestamp.
    2) It transforms a previous HardwareState.
    3) A new Version node is created.
    4) A new HardwareState instance is produced.

Event describes the change.
Version anchors it in time.
HardwareState stores the new world model.


Long-Term Stability Rule
------------------------

If a modification changes the semantic understanding
of the hardware world, it MUST be represented as an Event.

If it is merely an internal implementation detail,
it must NOT generate an Event.

Event is the backbone of temporal correctness
in the system.
"""