# from dataclasses import dataclass
# from datetime import datetime
# from typing import Optional


# @dataclass(frozen=True)
# class Version:
#     """
#     A node in the state evolution graph.

#     Defines the temporal coordinate of a HardwareState.
#     """

#     # 唯一标识（不可变）
#     id: str

#     # 父版本（允许 None 表示初始状态）
#     parent_id: Optional[str]

#     # 触发该版本生成的事件 ID
#     event_id: Optional[str]

#     # 事件发生的物理时间
#     physical_time: datetime

#     # 状态适用区间起点
#     valid_from: datetime

#     # 状态适用区间终点（None 表示当前仍有效）
#     valid_until: Optional[datetime]


"""
Version Model
=============

Concept
-------

`Version` defines the temporal coordinate of a `HardwareState`.

It is NOT:
    - a simple incrementing number
    - a calibration round counter
    - a database primary key
    - a storage-layer artifact

It IS:
    - a node in the state evolution graph
    - a temporal anchor of a hardware world model
    - the bridge between physical time and state transitions


Philosophy
----------

HardwareState does not change continuously with time.
It changes discretely when Events occur.

    State_{n+1} = f(State_n, Event_n)

A Version marks the existence of State_{n+1}
as a distinct node in the evolution graph.

Physical time does NOT directly mutate state.
Events mutate state.
Version records the result.


Three-Layer Temporal Model
--------------------------

1) Physical Time (continuous)
   - Wall clock time
   - When calibration or inference occurred
   - Used for drift analysis and reporting

2) Event (discrete change)
   - Calibration
   - Model update
   - Re-inference
   - Topology change
   - Any operation that modifies world knowledge

3) Version (state coordinate)
   - Identifies the new state created by an Event
   - Links to its parent version
   - Defines its validity time window


Graph Structure
---------------

Versions form a directed acyclic graph (DAG):

    S0 --E1--> S1 --E2--> S2
                 \
                  --E3--> S2b

This allows:
    - branching calibration strategies
    - alternative modeling assumptions
    - rollback and comparison
    - long-term evolution tracking


Validity Window
---------------

Each Version defines a time interval:

    valid_from  <=  physical time  <  valid_until

This represents when the corresponding HardwareState
is considered applicable in the real world.

When a new Version is created:
    - The previous version's `valid_until` should be closed.
    - The new version's `valid_from` begins.


Design Constraints
------------------

- Version must be immutable.
- Version must not store large data.
- Version must not contain hardware parameters.
- Version must not depend on storage implementation.
- Version must not embed Event content (only reference it).

It should remain small, stable, and domain-pure.


Why This Matters
----------------

Without a well-defined Version model:

    - State evolution becomes overwrite-based.
    - Calibration history becomes ambiguous.
    - Drift tracking becomes unreliable.
    - Parallel model exploration becomes unsafe.

Version is the backbone of temporal correctness
in the hardware world model.
"""