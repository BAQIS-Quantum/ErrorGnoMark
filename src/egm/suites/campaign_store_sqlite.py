from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional, Tuple


class CampaignSQLiteStore:
    """
    SQLite store for campaign/job/circuit records.

    The primary key is (campaign_name, job_name, circuit_name).
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_name TEXT NOT NULL,
                    job_name TEXT NOT NULL,
                    circuit_name TEXT NOT NULL,
                    campaign_id TEXT,
                    job_id TEXT,
                    local_id TEXT,
                    remote_id TEXT,
                    submit_payload TEXT,
                    result_payload TEXT,
                    submit_time_utc TEXT,
                    fetch_time_utc TEXT,
                    submit_state TEXT,
                    fetch_state TEXT,
                    server_status TEXT,
                    error_kind TEXT,
                    error_msg TEXT,
                    UNIQUE (campaign_name, job_name, circuit_name)
                )
                """
            )
            cols = {row[1] for row in conn.execute("PRAGMA table_info(records);").fetchall()}
            if "campaign_id" not in cols:
                conn.execute("ALTER TABLE records ADD COLUMN campaign_id TEXT;")
            if "job_id" not in cols:
                conn.execute("ALTER TABLE records ADD COLUMN job_id TEXT;")
            if "submit_state" not in cols:
                conn.execute("ALTER TABLE records ADD COLUMN submit_state TEXT;")
            if "fetch_state" not in cols:
                conn.execute("ALTER TABLE records ADD COLUMN fetch_state TEXT;")
            if "server_status" not in cols:
                conn.execute("ALTER TABLE records ADD COLUMN server_status TEXT;")
            if "error_kind" not in cols:
                conn.execute("ALTER TABLE records ADD COLUMN error_kind TEXT;")
            if "error_msg" not in cols:
                conn.execute("ALTER TABLE records ADD COLUMN error_msg TEXT;")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_campaign ON records (campaign_name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_job ON records (campaign_name, job_name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ids ON records (campaign_id, job_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_states ON records (submit_state, fetch_state)"
            )

    def upsert_submit(
        self,
        campaign_name: str,
        job_name: str,
        circuit_name: str,
        *,
        campaign_id: Optional[str],
        job_id: Optional[str],
        local_id: Optional[str],
        remote_id: Optional[str],
        submit_payload: Dict[str, Any],
        submit_time_utc: Optional[str],
        submit_state: Optional[str],
        fetch_state: Optional[str],
        server_status: Optional[str],
        error_kind: Optional[str],
        error_msg: Optional[str],
    ) -> None:
        payload_text = json.dumps(submit_payload, ensure_ascii=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO records (
                    campaign_name, job_name, circuit_name,
                    campaign_id, job_id,
                    local_id, remote_id, submit_payload, submit_time_utc
                    , submit_state, fetch_state, server_status, error_kind, error_msg
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(campaign_name, job_name, circuit_name)
                DO UPDATE SET
                    campaign_id=excluded.campaign_id,
                    job_id=excluded.job_id,
                    local_id=excluded.local_id,
                    remote_id=excluded.remote_id,
                    submit_payload=excluded.submit_payload,
                    submit_time_utc=excluded.submit_time_utc,
                    submit_state=excluded.submit_state,
                    fetch_state=COALESCE(records.fetch_state, excluded.fetch_state),
                    server_status=COALESCE(records.server_status, excluded.server_status),
                    error_kind=excluded.error_kind,
                    error_msg=excluded.error_msg
                """,
                (
                    campaign_name,
                    job_name,
                    circuit_name,
                    campaign_id,
                    job_id,
                    local_id,
                    remote_id,
                    payload_text,
                    submit_time_utc,
                    submit_state,
                    fetch_state,
                    server_status,
                    error_kind,
                    error_msg,
                ),
            )

    def upsert_result(
        self,
        campaign_name: str,
        job_name: str,
        circuit_name: str,
        *,
        campaign_id: Optional[str],
        job_id: Optional[str],
        remote_id: Optional[str],
        result_payload: Dict[str, Any],
        fetch_time_utc: Optional[str],
        submit_state: Optional[str],
        fetch_state: Optional[str],
        server_status: Optional[str],
        error_kind: Optional[str],
        error_msg: Optional[str],
    ) -> None:
        payload_text = json.dumps(result_payload, ensure_ascii=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO records (
                    campaign_name, job_name, circuit_name,
                    campaign_id, job_id,
                    remote_id, result_payload, fetch_time_utc,
                    submit_state, fetch_state, server_status, error_kind, error_msg
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(campaign_name, job_name, circuit_name)
                DO UPDATE SET
                    campaign_id=excluded.campaign_id,
                    job_id=excluded.job_id,
                    remote_id=excluded.remote_id,
                    result_payload=excluded.result_payload,
                    fetch_time_utc=excluded.fetch_time_utc,
                    submit_state=COALESCE(records.submit_state, excluded.submit_state),
                    fetch_state=excluded.fetch_state,
                    server_status=excluded.server_status,
                    error_kind=excluded.error_kind,
                    error_msg=excluded.error_msg
                """,
                (
                    campaign_name,
                    job_name,
                    circuit_name,
                    campaign_id,
                    job_id,
                    remote_id,
                    payload_text,
                    fetch_time_utc,
                    submit_state,
                    fetch_state,
                    server_status,
                    error_kind,
                    error_msg,
                ),
            )

    def find_by_labels(
        self, campaign_name: str, job_name: str, circuit_name: str
    ) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM records
                WHERE campaign_name=? AND job_name=? AND circuit_name=?
                """,
                (campaign_name, job_name, circuit_name),
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def list_campaign(self, campaign_name: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM records WHERE campaign_name=? ORDER BY id",
                (campaign_name,),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def list_job(self, campaign_name: str, job_name: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM records
                WHERE campaign_name=? AND job_name=?
                ORDER BY id
                """,
                (campaign_name, job_name),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def register_submit_records(self, records: List[Dict[str, Any]]) -> None:
        for rec in records:
            labels = rec.get("labels") or {}
            submit_state, fetch_state, server_status, error_kind, error_msg = self._derive_states_from_submit_record(rec)
            self.upsert_submit(
                labels.get("campaign_name", "campaign"),
                labels.get("job_name", "job"),
                labels.get("circuit_name", "circuit"),
                campaign_id=labels.get("campaign_id"),
                job_id=labels.get("job_id"),
                local_id=rec.get("local_id"),
                remote_id=(rec.get("quark_payload") or {}).get("remote_id"),
                submit_payload=rec,
                submit_time_utc=(rec.get("quark_payload") or {}).get("timestamp_utc"),
                submit_state=submit_state,
                fetch_state=fetch_state,
                server_status=server_status,
                error_kind=error_kind,
                error_msg=error_msg,
            )

    def register_fetch_records(
        self,
        fetch_records: List[tuple],
        submit_records: List[Dict[str, Any]],
    ) -> None:
        remote_to_labels = {}
        for rec in submit_records:
            remote_id = (rec.get("quark_payload") or {}).get("remote_id")
            if remote_id is not None:
                remote_to_labels[str(remote_id)] = rec.get("labels") or {}

        for remote_id, request_ts, res, response_ts in fetch_records:
            labels = remote_to_labels.get(str(remote_id), {})
            submit_state, fetch_state, server_status, error_kind, error_msg = self._derive_states_from_fetch_payload(res)
            self.upsert_result(
                labels.get("campaign_name", "campaign"),
                labels.get("job_name", "job"),
                labels.get("circuit_name", "circuit"),
                campaign_id=labels.get("campaign_id"),
                job_id=labels.get("job_id"),
                remote_id=str(remote_id) if remote_id is not None else None,
                result_payload={"request_ts": request_ts, "response_ts": response_ts, "res": res},
                fetch_time_utc=response_ts,
                submit_state=submit_state,
                fetch_state=fetch_state,
                server_status=server_status,
                error_kind=error_kind,
                error_msg=error_msg,
            )

    def get_pending_fetch_submit_records(
        self,
        *,
        campaign_name: str,
        job_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return minimal submit_records (JobSubmitFetch-shaped dicts) for tasks that:
        - belong to the given campaign[/job]
        - have remote_id
        - have no result yet
        """
        where = "campaign_name=? AND remote_id IS NOT NULL AND remote_id!='' AND result_payload IS NULL"
        params: list = [campaign_name]
        if job_name:
            where += " AND job_name=?"
            params.append(job_name)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT campaign_name, job_name, circuit_name,
                       campaign_id, job_id, local_id, remote_id
                FROM records
                WHERE {where}
                ORDER BY id
                """,
                tuple(params),
            ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            labels = {
                "campaign_name": r["campaign_name"],
                "job_name": r["job_name"],
                "circuit_name": r["circuit_name"],
                "campaign_id": r["campaign_id"],
                "job_id": r["job_id"],
            }
            out.append(
                {
                    "local_id": r["local_id"],
                    "labels": labels,
                    "quark_payload": {"remote_id": r["remote_id"]},
                }
            )
        return out

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        if data.get("submit_payload"):
            data["submit_payload"] = json.loads(data["submit_payload"])
        if data.get("result_payload"):
            data["result_payload"] = json.loads(data["result_payload"])
        return data

    @staticmethod
    def _short_error(msg: Optional[str], limit: int = 512) -> Optional[str]:
        if not msg:
            return None
        s = str(msg)
        return s if len(s) <= limit else s[: limit - 3] + "..."

    def _derive_states_from_submit_record(
        self, rec: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Derive submit/fetch classification from a JobSubmitFetch submit record.
        """
        quark_payload = rec.get("quark_payload") or {}
        remote_id = quark_payload.get("remote_id")
        submit_error = rec.get("error") or quark_payload.get("submit_error")
        if submit_error or not remote_id:
            return "LOCAL_ERROR", "NOT_FETCHED", None, "LOCAL_SUBMIT_ERROR", self._short_error(submit_error)
        return "SUBMITTED", "NOT_FETCHED", None, None, None

    def _derive_states_from_fetch_payload(
        self, res: Optional[Dict[str, Any]]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Derive fetch classification from result dict returned by Task.result().
        """
        if not isinstance(res, dict):
            return None, "FETCHED_ERROR", None, "REMOTE_RESULT_ERROR", "Non-dict result"
        server_status = res.get("status")
        error_msg = None
        for k in ("error", "message", "detail", "description"):
            if k in res and res.get(k):
                error_msg = str(res.get(k))
                break
        if error_msg or (isinstance(server_status, str) and server_status.lower() in ("failed", "error")):
            return None, "FETCHED_ERROR", server_status, "REMOTE_RESULT_ERROR", self._short_error(error_msg or server_status)
        return None, "FETCHED_OK", server_status, None, None
