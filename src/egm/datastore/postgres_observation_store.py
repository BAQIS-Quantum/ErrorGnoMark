"""
PostgreSQL-backed :class:`ObservationStore` for Phase 1 workflow observations.

Each ``save_observation`` writes:

- one ``benchmark_run`` row (run envelope), and
- one ``observation_record`` row with ``value_json`` equal to the
  :class:`~egm.datastore.observation_store.ObservationPersistenceDict`` payload,
  ``producer_type`` = ``benchmark_run``, and ``subject_type`` = ``chip``.

Requires ``psycopg`` and a database with ``db/phase1`` schema + seed applied.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from egm.datastore.observation_store import KEYS, ObservationPersistenceDict, ObservationStore
from egm.datastore.phase1_pg_constants import METRIC_EGM_TASK_OBSERVATION_V1, SEED_SOURCE_ID

try:
    from psycopg import Connection
    from psycopg.rows import dict_row
    from psycopg.types.json import Json
except ImportError:  # pragma: no cover - optional dependency
    Connection = Any  # type: ignore[misc, assignment]
    dict_row = Any  # type: ignore[misc, assignment]
    Json = Any  # type: ignore[misc, assignment]


def _require_psycopg() -> None:
    if Connection is Any:  # pragma: no cover
        raise ImportError(
            "PostgresObservationStore requires the 'psycopg' package. "
            "Install optional dev deps or: pip install 'psycopg[binary]>=3.2'"
        )


def _parse_uuid(obs_id: str) -> uuid.UUID:
    if len(obs_id) == 32 and all(c in "0123456789abcdefABCDEF" for c in obs_id):
        return uuid.UUID(hex=obs_id)
    return uuid.UUID(obs_id)


def _uuid_return(obs_id: uuid.UUID) -> str:
    return obs_id.hex


def _execution_to_run_status(execution_status: str) -> str:
    if execution_status == "ok":
        return "succeeded"
    return "failed"


def _observation_time(rec: ObservationPersistenceDict) -> datetime:
    raw = rec.get(KEYS.observation_time)
    if raw is None:
        return datetime.now(timezone.utc)
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str):
        s = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    raise ValueError("observation_time must be ISO string, datetime, or None")


class PostgresObservationStore:
    """
    ObservationStore backed by ``benchmark_run`` + ``observation_record`` (DDL v1).

    ``chip_name`` in the persistence dict must match a seeded ``chip.chip_name``
    (e.g. ``chip-alpha``).
    """

    def __init__(self, dsn: str) -> None:
        _require_psycopg()
        self._dsn = dsn

    def _connect(self) -> Connection:
        return Connection.connect(self._dsn, row_factory=dict_row)

    def save_observation(self, record: ObservationPersistenceDict) -> str:
        chip_name = record.get(KEYS.chip_name)
        if not chip_name or not isinstance(chip_name, str):
            raise ValueError("ObservationPersistenceDict must include string chip_name for PG store")

        obs_time = _observation_time(record)
        bench_status = _execution_to_run_status(str(record.get(KEYS.execution_status, "")))
        protocol = str(record.get(KEYS.protocol, "unknown"))

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT chip_id FROM chip WHERE chip_name = %(name)s LIMIT 1",
                    {"name": chip_name},
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(f"No chip row for chip_name={chip_name!r}")
                chip_id = row["chip_id"]

                cur.execute(
                    """
                    INSERT INTO benchmark_run (
                        benchmark_name,
                        benchmark_version_id,
                        chip_id,
                        target_scope_id,
                        input_config_json,
                        result_ref,
                        status,
                        start_time,
                        end_time,
                        ingested_at,
                        source_id,
                        payload_json
                    ) VALUES (
                        %(benchmark_name)s,
                        NULL,
                        %(chip_id)s,
                        NULL,
                        '{}'::jsonb,
                        NULL,
                        %(status)s::run_status_enum,
                        %(start_time)s,
                        %(end_time)s,
                        now(),
                        %(source_id)s::uuid,
                        '{}'::jsonb
                    )
                    RETURNING benchmark_run_id
                    """,
                    {
                        "benchmark_name": protocol,
                        "chip_id": str(chip_id),
                        "status": bench_status,
                        "start_time": obs_time,
                        "end_time": obs_time,
                        "source_id": SEED_SOURCE_ID,
                    },
                )
                br = cur.fetchone()
                assert br is not None
                benchmark_run_id = br["benchmark_run_id"]

                cur.execute(
                    """
                    INSERT INTO observation_record (
                        chip_id,
                        subject_type,
                        subject_id,
                        scope_id,
                        metric_definition_id,
                        producer_type,
                        producer_id,
                        value_numeric,
                        value_text,
                        value_json,
                        unit,
                        quality_flag,
                        observation_time,
                        effective_from,
                        effective_to,
                        published_at,
                        ingested_at,
                        source_id
                    ) VALUES (
                        %(chip_id)s::uuid,
                        'chip'::subject_type_enum,
                        %(subject_id)s::uuid,
                        NULL,
                        %(metric_id)s::uuid,
                        'benchmark_run'::producer_type_enum,
                        %(producer_id)s::uuid,
                        NULL,
                        NULL,
                        %(value_json)s,
                        NULL,
                        'raw'::quality_flag_enum,
                        %(observation_time)s,
                        NULL,
                        NULL,
                        NULL,
                        now(),
                        %(source_id)s::uuid
                    )
                    RETURNING observation_record_id
                    """,
                    {
                        "chip_id": str(chip_id),
                        "subject_id": str(chip_id),
                        "metric_id": METRIC_EGM_TASK_OBSERVATION_V1,
                        "producer_id": str(benchmark_run_id),
                        "value_json": Json(dict(record)),
                        "observation_time": obs_time,
                        "source_id": SEED_SOURCE_ID,
                    },
                )
                orow = cur.fetchone()
                assert orow is not None
                oid = orow["observation_record_id"]
            conn.commit()
        return _uuid_return(oid)

    def load_observation(self, observation_id: str) -> Optional[ObservationPersistenceDict]:
        oid = _parse_uuid(observation_id)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT value_json
                    FROM observation_record
                    WHERE observation_record_id = %(id)s::uuid
                      AND metric_definition_id = %(metric)s::uuid
                    """,
                    {"id": str(oid), "metric": METRIC_EGM_TASK_OBSERVATION_V1},
                )
                r = cur.fetchone()
        if r is None:
            return None
        payload = r["value_json"]
        if not isinstance(payload, dict):
            return None
        return dict(payload)  # type: ignore[return-value]

    def list_observation_ids(self) -> List[str]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT observation_record_id
                    FROM observation_record
                    WHERE metric_definition_id = %(metric)s::uuid
                    ORDER BY ingested_at
                    """,
                    {"metric": METRIC_EGM_TASK_OBSERVATION_V1},
                )
                rows = cur.fetchall()
        return [_uuid_return(r["observation_record_id"]) for r in rows]

    def filter_observations(self, **equals: Any) -> List[ObservationPersistenceDict]:
        allowed = {"task_id", "plan_id", "protocol", "backend_name", "chip_name"}
        unknown = set(equals.keys()) - allowed
        if unknown:
            raise ValueError(f"Unsupported filter keys: {sorted(unknown)}")

        clauses: List[str] = ["metric_definition_id = %(metric)s::uuid"]
        params: Dict[str, Any] = {"metric": METRIC_EGM_TASK_OBSERVATION_V1}
        for k in allowed:
            if k not in equals or equals[k] is None:
                continue
            pname = f"eq_{k}"
            clauses.append(f"value_json->>'{k}' = %({pname})s")
            params[pname] = str(equals[k])

        where_sql = " AND ".join(clauses)
        sql = f"SELECT value_json FROM observation_record WHERE {where_sql}"

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        out: List[ObservationPersistenceDict] = []
        for r in rows:
            v = r["value_json"]
            if isinstance(v, dict):
                out.append(dict(v))
        return out


def resolve_chip_id_for_smoke(dsn: str, chip_name: str = "chip-alpha") -> str:
    """
    Return ``chip_id`` for a known demo chip (defaults to ``chip-alpha``).

    Used by PG smoke when asserting FK alignment; matches ``chip_name`` in seed
    ``010_minimal_demo.sql`` (default ``chip-alpha``).
    """
    _require_psycopg()
    with Connection.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT chip_id::text AS chip_id FROM chip WHERE chip_name = %s",
                (chip_name,),
            )
            row = cur.fetchone()
    if row is None:
        raise ValueError(f"No chip named {chip_name!r}")
    cid = row["chip_id"]
    return str(cid)


ObservationStore.register(PostgresObservationStore)
