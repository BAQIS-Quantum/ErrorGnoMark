"""
Roadmap: circuit-level execution payload persistence & query-facing raw data.

Status: planning only — nothing here is wired into runtime imports by default.
Open this module when picking up datastore / Phase 1 persistence follow-ups.

Why here
--------
- Hot path today: :class:`egm.schemas.results.execution.TaskExecutionResult` already holds
  per-circuit ``ideal_noisy_pairs`` (ideal probs + noisy counts) in memory after
  :func:`egm.execution.plan_runner.run_plan`.
- Long-term: persist **task-level summaries** (already sketched via observation records)
  plus **circuit-level cold payloads** (large dicts) with refs / object storage, aligned
  with Phase 1 DDL ``payload_ref`` / JSONB patterns in
  ``notes-private/.../p1-step1-...DDL...``.

TODO batches (implement in dedicated PRs; keep this list updated when done)
------------------------------------------------------------------------------
1. **Schemas** — Add a typed or key-stable contract for one circuit’s persisted bundle,
   e.g. ``protocol``, ``circuit_index``, ``shots``, ``ideal_probabilities`` (sparse map),
   ``observed_counts``, optional ``circuit_fingerprint`` / metadata hash. Place under
   ``egm/schemas/results/`` (name TBD: ``execution_payload.py`` or extend execution
   result docs only; avoid breaking ``TaskExecutionResult`` callers).

2. **Serialization** — ``egm.services.serialization``: map in-memory pairs → persistence
   dict + optional external blob write hook (returns ``payload_ref``).

3. **Datastore** — Extend :class:`egm.datastore.observation_store.ObservationStore` or add
   a sibling protocol (e.g. ``CircuitExecutionPayloadStore``) with save/load/list by
   ``(observation_id, circuit_index)`` or ``circuit_payload_id``; keep
   ``datastore/`` free of ``egm.domain.*`` imports.

4. **Ingest service** — Orchestrate: after ``run_plan``, walk ``ideal_noisy_pairs``,
   write summaries to existing observation row + attach refs / child rows per Phase 1
   table design once Postgres exists.

5. **Query service** — Read path for “drill down to raw distributions” vs “list task
   summaries only”; pagination / max key limits for UI.

6. **Demo / smoke** — Optional: print preview from **memory** immediately after run;
   stricter path: save → reload → print to prove round-trip (same as production read).

7. **XEB-specific preview** — If reused beyond smoke, small helper module under
   ``egm.execution`` or ``egm.services.debug``; gate on ``protocol == \"XEB\"``.

Cross-links (repo-relative)
---------------------------
- Phase 1 scope: ``notes-private/dairy/2026-4月/20260425-实施方案/phase1- 查询功能/``
- Current in-memory MVP: ``egm.datastore.observation_store_memory``,
  ``egm.services.serialization.observation_record``,
  ``egm.domain.records.task_observation_record``.
"""

__all__: list[str] = []
