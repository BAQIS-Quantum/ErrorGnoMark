from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from egm.core.backends.Real_Quark_Backend import RealQuarkBackend
from egm.core.circuits.circuit import QuantumCircuit


class JobSubmitFetch:
    """
    Job submit/fetch helper for single-circuit backends.

    - job_submit: submit a list of circuits
    - job_fetch: fetch results for a list of remote ids
    """

    def __init__(self, backend: RealQuarkBackend, results_dir: Optional[str] = None) -> None:
        self.backend = backend
        self.results_dir = self._resolve_results_dir(results_dir)

    def job_submit(
        self,
        circuits: List[QuantumCircuit],
        shots: int,
        args: Dict[str, Any],
        *,
        campaign_name: Optional[str] = None,
        job_name: Optional[str] = None,
        campaign_id: Optional[str] = None,
        job_id: Optional[str] = None,
        show_progress: bool = False,
    ) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        campaign_id = campaign_id or uuid.uuid4().hex
        job_id = job_id or uuid.uuid4().hex
        depth_counters: Dict[Any, int] = {}
        iterator = enumerate(circuits)
        if show_progress:
            try:
                from tqdm import tqdm
            except Exception:  # pragma: no cover - tqdm optional
                tqdm = None
            if tqdm:
                iterator = tqdm(iterator, total=len(circuits), desc="Submitting")
        for idx, circuit in iterator:
            meta = getattr(circuit, "metadata", {}) or {}
            depth = meta.get("depth") if isinstance(meta, dict) else None
            if depth is not None:
                depth_idx = depth_counters.get(depth, 0)
                depth_counters[depth] = depth_idx + 1
            else:
                depth_idx = idx
            labels = self._build_labels(
                circuit,
                idx,
                depth_idx,
                campaign_name,
                job_name,
                campaign_id,
                job_id,
            )
            self._attach_labels(circuit, labels)
            try:
                local_id, egm_payload, quark_payload = self.backend.submit(
                    circuit=circuit, shots=shots, args=args
                )
                record = {
                    "index": idx,
                    "local_id": local_id,
                    "egm_payload": egm_payload,
                    "quark_payload": quark_payload,
                    "labels": labels,
                }
                records.append(record)
                self._write_submission_files(record)
            except Exception as exc:
                record = {
                    "index": idx,
                    "local_id": None,
                    "egm_payload": None,
                    "quark_payload": None,
                    "labels": labels,
                    "error": str(exc),
                }
                records.append(record)
        return records

    def job_fetch(
        self,
        remote_ids: List[Any],
        *,
        submit_records: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Tuple[Any, str, Optional[Dict[str, Any]], str]]:
        results: List[Tuple[Any, str, Optional[Dict[str, Any]], str]] = []
        record_map = self._build_remote_map(submit_records)
        for remote_id in remote_ids:
            try:
                request_ts, res, response_ts = self.backend.fetch(remote_id)
                results.append((remote_id, request_ts, res, response_ts))
                record = record_map.get(str(remote_id))
                if record:
                    self._write_result_files(record, request_ts, res, response_ts)
            except Exception as exc:
                ts = self._utc_timestamp()
                results.append((remote_id, ts, {"error": str(exc)}, ts))
                record = record_map.get(str(remote_id))
                if record:
                    self._write_result_files(record, ts, {"error": str(exc)}, ts)
        return results

    @staticmethod
    def _utc_timestamp() -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def _resolve_results_dir(self, results_dir: Optional[str]) -> str:
        env_dir = os.getenv("EGM_DATASTORE_DIR")
        base = results_dir or env_dir
        if base:
            return os.path.abspath(os.path.expanduser(base))
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "datastore"))

    def _task_dir(self, local_id: str) -> str:
        task_dir = os.path.join(self.results_dir, local_id)
        os.makedirs(task_dir, exist_ok=True)
        return task_dir

    def _write_json(self, local_id: str, filename: str, payload: Dict[str, Any]) -> None:
        path = os.path.join(self._task_dir(local_id), filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _write_submission_files(self, record: Dict[str, Any]) -> None:
        local_id = record.get("local_id")
        if not local_id:
            return
        quark_payload = record.get("quark_payload") or {}
        submit_error = quark_payload.get("submit_error")
        remote_id = quark_payload.get("remote_id")
        submission = {
            "local_id": local_id,
            "labels": record.get("labels"),
            "egm_payload": record.get("egm_payload"),
            "quark_payload": quark_payload,
        }
        status = {
            "local_id": local_id,
            "remote_id": remote_id,
            "submitted": remote_id is not None and submit_error is None,
            "submit_error": submit_error,
            "timestamps": {
                "submitted_utc": quark_payload.get("timestamp_utc") or self._utc_timestamp(),
                "last_update_utc": self._utc_timestamp(),
            },
        }
        self._write_json(local_id, "submission_data.json", submission)
        self._write_json(local_id, "status.json", status)

    def _write_result_files(
        self,
        record: Dict[str, Any],
        request_ts: str,
        res: Optional[Dict[str, Any]],
        response_ts: str,
    ) -> None:
        local_id = record.get("local_id")
        if not local_id:
            return
        remote_id = (record.get("quark_payload") or {}).get("remote_id")
        result_payload = {
            "local_id": local_id,
            "remote_id": remote_id,
            "request_ts": request_ts,
            "response_ts": response_ts,
            "raw_result": res,
        }
        status = {
            "local_id": local_id,
            "remote_id": remote_id,
            "submitted": remote_id is not None,
            "timestamps": {
                "last_update_utc": response_ts,
            },
        }
        # Keep a single, user-facing result file name.
        self._write_json(local_id, "result.json", result_payload)
        self._write_json(local_id, "status.json", status)

    @staticmethod
    def _build_remote_map(
        submit_records: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Dict[str, Any]]:
        record_map: Dict[str, Dict[str, Any]] = {}
        if not submit_records:
            return record_map
        for rec in submit_records:
            remote_id = (rec.get("quark_payload") or {}).get("remote_id")
            if remote_id is not None:
                record_map[str(remote_id)] = rec
        return record_map

    @staticmethod
    def _build_labels(
        circuit: QuantumCircuit,
        index: int,
        depth_index: int,
        campaign_name: Optional[str],
        job_name: Optional[str],
        campaign_id: str,
        job_id: str,
    ) -> Dict[str, str]:
        depth = None
        meta = getattr(circuit, "metadata", {}) or {}
        if isinstance(meta, dict):
            depth = meta.get("depth")
        if depth is not None:
            circuit_name = f"depth_{depth}_no_{depth_index}"
        else:
            circuit_name = f"circuit_{index}"
        return {
            "campaign_name": campaign_name or "campaign",
            "job_name": job_name or "job",
            "circuit_name": circuit_name,
            "campaign_id": campaign_id,
            "job_id": job_id,
        }

    @staticmethod
    def _attach_labels(circuit: QuantumCircuit, labels: Dict[str, str]) -> None:
        if not hasattr(circuit, "metadata") or circuit.metadata is None:
            circuit.metadata = {}
        circuit.metadata.update(labels)
