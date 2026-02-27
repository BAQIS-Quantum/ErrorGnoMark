from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from egm.core.backends.quark_result_translator import quark_result_to_counts
from egm.core.backends.ideal_backend import IdealBackend
from egm.core.circuits.convertor import deserialize_circuit
from egm.suites.campaign_store_sqlite import CampaignSQLiteStore


def load_submit_fetch_from_datastore_dir(
    datastore_dir: str,
) -> Tuple[List[Dict[str, Any]], List[Tuple[Any, str, Optional[Dict[str, Any]], str]]]:
    """
    Load submit/fetch records from the on-disk datastore created by egm.suites.JobSubmitFetch.

    The directory is expected to contain subfolders like:
      local_<timestamp>_<suffix>/
        submission_data.json
        result.json

    Returns
    -------
    submit_records : List[Dict[str, Any]]
        Minimal records containing egm_payload and remote_id (api_token is stripped).
    fetch_records : List[Tuple[Any, str, Optional[Dict[str, Any]], str]]
        (remote_id, request_ts, raw_result, response_ts) tuples.
    """
    base = Path(datastore_dir)
    submit_records: List[Dict[str, Any]] = []
    fetch_records: List[Tuple[Any, str, Optional[Dict[str, Any]], str]] = []

    if not base.exists():
        raise FileNotFoundError(f"Datastore dir not found: {datastore_dir}")

    task_dirs = [p for p in base.iterdir() if p.is_dir() and p.name.startswith("local_")]
    task_dirs.sort(key=lambda p: p.stat().st_mtime)

    for d in task_dirs:
        sub_path = d / "submission_data.json"
        res_path = d / "result.json"

        if sub_path.exists():
            sub = json.loads(sub_path.read_text(encoding="utf-8"))
            quark_payload = sub.get("quark_payload") or {}
            submit_records.append(
                {
                    "local_id": sub.get("local_id"),
                    "labels": sub.get("labels") or {},
                    "egm_payload": sub.get("egm_payload") or {},
                    "quark_payload": {"remote_id": quark_payload.get("remote_id")},
                }
            )

        if res_path.exists():
            res = json.loads(res_path.read_text(encoding="utf-8"))
            fetch_records.append(
                (
                    res.get("remote_id"),
                    res.get("request_ts") or "",
                    res.get("raw_result"),
                    res.get("response_ts") or "",
                )
            )

    return submit_records, fetch_records


def list_campaign_names_from_sqlite(db_path: str) -> List[str]:
    store = CampaignSQLiteStore(db_path)
    with store._connect() as conn:  # noqa: SLF001 - intentional: single-file helper
        rows = conn.execute(
            "SELECT DISTINCT campaign_name FROM records ORDER BY campaign_name"
        ).fetchall()
    return [r[0] for r in rows if r and r[0]]


def list_campaign_stats_from_sqlite(db_path: str) -> List[Dict[str, Any]]:
    """
    Return per-campaign counters so you can pick a campaign that already has fetched results.
    """
    store = CampaignSQLiteStore(db_path)
    with store._connect() as conn:  # noqa: SLF001 - intentional: single-file helper
        rows = conn.execute(
            """
            SELECT campaign_name,
                   COUNT(*) AS total,
                   SUM(CASE WHEN result_payload IS NOT NULL THEN 1 ELSE 0 END) AS fetched_any,
                   SUM(CASE WHEN fetch_state='FETCHED_OK' THEN 1 ELSE 0 END) AS fetched_ok
            FROM records
            GROUP BY campaign_name
            ORDER BY fetched_ok DESC, fetched_any DESC, total DESC, campaign_name
            """
        ).fetchall()
    return [
        {
            "campaign_name": r["campaign_name"],
            "total": int(r["total"] or 0),
            "fetched_any": int(r["fetched_any"] or 0),
            "fetched_ok": int(r["fetched_ok"] or 0),
        }
        for r in rows
        if r and r["campaign_name"]
    ]


def list_jobs_from_sqlite(
    db_path: str,
    *,
    campaign_name: str,
) -> List[str]:
    """
    List distinct job_name values for a campaign.
    """
    store = CampaignSQLiteStore(db_path)
    with store._connect() as conn:  # noqa: SLF001 - intentional: single-file helper
        rows = conn.execute(
            """
            SELECT DISTINCT job_name
            FROM records
            WHERE campaign_name=?
            ORDER BY job_name
            """,
            (campaign_name,),
        ).fetchall()
    return [r[0] for r in rows if r and r[0]]

def _sanitize_submit_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive fields (e.g. api_token) from a stored submit record.
    """
    out = dict(rec)
    qp = dict(out.get("quark_payload") or {})
    args = dict(qp.get("args") or {})
    if "api_token" in args:
        args.pop("api_token", None)
    if args:
        qp["args"] = args
    else:
        qp.pop("args", None)
    out["quark_payload"] = qp
    return out


def load_submit_fetch_from_sqlite(
    db_path: str,
    *,
    campaign_name: Optional[str] = None,
    job_name: Optional[str] = None,
    only_fetched_ok: bool = True,
) -> Tuple[List[Dict[str, Any]], List[Tuple[Any, str, Optional[Dict[str, Any]], str]]]:
    """
    Load submit/fetch records from CampaignSQLiteStore DB.

    Parameters
    ----------
    db_path:
        Path to sqlite db (e.g. datasotore_copy/egm_campaign.db)
    campaign_name:
        Filter by campaign. If None, loads the most recently written campaign.
    job_name:
        Optional job filter.
    only_fetched_ok:
        If True, only include records whose fetch_state == 'FETCHED_OK'.
        If False, includes any record with result_payload present.
    """
    store = CampaignSQLiteStore(db_path)

    if campaign_name is None:
        with store._connect() as conn:  # noqa: SLF001 - intentional: single-file helper
            row = conn.execute(
                """
                SELECT campaign_name
                FROM records
                WHERE fetch_state='FETCHED_OK' AND campaign_name IS NOT NULL AND campaign_name!=''
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
            if not row or not row[0]:
                row = conn.execute(
                    """
                    SELECT campaign_name
                    FROM records
                    WHERE campaign_name IS NOT NULL AND campaign_name!=''
                    ORDER BY id DESC
                    LIMIT 1
                    """
                ).fetchone()
        if not row or not row[0]:
            return [], []
        campaign_name = str(row[0])

    rows = store.list_job(campaign_name, job_name) if job_name else store.list_campaign(campaign_name)

    submit_records: List[Dict[str, Any]] = []
    fetch_records: List[Tuple[Any, str, Optional[Dict[str, Any]], str]] = []

    for r in rows:
        submit_payload = r.get("submit_payload") or {}
        if isinstance(submit_payload, dict) and submit_payload:
            submit_records.append(_sanitize_submit_record(submit_payload))

        result_payload = r.get("result_payload")
        if not isinstance(result_payload, dict) or not result_payload:
            continue

        if only_fetched_ok and r.get("fetch_state") != "FETCHED_OK":
            continue

        res = result_payload.get("res")
        fetch_records.append(
            (
                r.get("remote_id"),
                result_payload.get("request_ts") or "",
                res if isinstance(res, dict) else None,
                result_payload.get("response_ts") or "",
            )
        )

    return submit_records, fetch_records


def _group_records_by_job(
    rows: List[Dict[str, Any]],
    *,
    only_fetched_ok: bool,
) -> Dict[str, Tuple[List[Dict[str, Any]], List[Tuple[Any, str, Optional[Dict[str, Any]], str]]]]:
    grouped: Dict[str, Tuple[List[Dict[str, Any]], List[Tuple[Any, str, Optional[Dict[str, Any]], str]]]] = {}
    for r in rows:
        job = r.get("job_name") or "job"
        submit_records, fetch_records = grouped.setdefault(job, ([], []))

        submit_payload = r.get("submit_payload") or {}
        if isinstance(submit_payload, dict) and submit_payload:
            submit_records.append(_sanitize_submit_record(submit_payload))

        result_payload = r.get("result_payload")
        if not isinstance(result_payload, dict) or not result_payload:
            continue

        if only_fetched_ok and r.get("fetch_state") != "FETCHED_OK":
            continue

        res = result_payload.get("res")
        fetch_records.append(
            (
                r.get("remote_id"),
                result_payload.get("request_ts") or "",
                res if isinstance(res, dict) else None,
                result_payload.get("response_ts") or "",
            )
        )
    return grouped


def rb_stitched_results_from_submit_fetch(
    submit_records: List[Dict[str, Any]],
    fetch_records: List[Tuple[Any, str, Optional[Dict[str, Any]], str]],
    *,
    prefer_corrected: bool = False,
    reverse_bitstring: bool = False,
) -> List[Dict[str, Any]]:
    """
    Build the exact structure expected by egm.core.analysis.rb.analyze_rb_standard():

        [{"data": {bitstring: count}, "metadata": {...}}, ...]

    Inputs are the records returned by egm.suites.JobSubmitFetch.job_submit/job_fetch.
    """
    fetch_map: Dict[str, Optional[Dict[str, Any]]] = {str(rid): res for rid, _rt, res, _st in fetch_records}

    out: List[Dict[str, Any]] = []
    for rec in submit_records:
        quark_payload = rec.get("quark_payload") or {}
        remote_id = quark_payload.get("remote_id")
        egm_payload = rec.get("egm_payload") or {}
        egm_circuit = egm_payload.get("egm_circuit") or {}
        num_qubits = int(egm_circuit.get("num_qubits") or len(egm_circuit.get("qubits") or []))
        metadata = egm_circuit.get("metadata") or {}
        raw = fetch_map.get(str(remote_id)) if remote_id is not None else None

        data_map = quark_result_to_counts(
            raw or {},
            num_qubits=num_qubits,
            prefer_corrected=prefer_corrected,
            reverse_bitstring=reverse_bitstring,
        )

        out.append({"data": data_map, "metadata": dict(metadata) if isinstance(metadata, dict) else {}})
    return out


def rb_stitched_results_from_datastore_dir(
    datastore_dir: str,
    *,
    prefer_corrected: bool = False,
    reverse_bitstring: bool = False,
) -> List[Dict[str, Any]]:
    submit_records, fetch_records = load_submit_fetch_from_datastore_dir(datastore_dir)
    return rb_stitched_results_from_submit_fetch(
        submit_records,
        fetch_records,
        prefer_corrected=prefer_corrected,
        reverse_bitstring=reverse_bitstring,
    )


def rb_stitched_results_from_sqlite(
    db_path: str,
    *,
    campaign_name: Optional[str] = None,
    job_name: Optional[str] = None,
    prefer_corrected: bool = False,
    reverse_bitstring: bool = False,
    only_fetched_ok: bool = True,
) -> List[Dict[str, Any]]:
    submit_records, fetch_records = load_submit_fetch_from_sqlite(
        db_path,
        campaign_name=campaign_name,
        job_name=job_name,
        only_fetched_ok=only_fetched_ok,
    )
    return rb_stitched_results_from_submit_fetch(
        submit_records,
        fetch_records,
        prefer_corrected=prefer_corrected,
        reverse_bitstring=reverse_bitstring,
    )


def rb_stitched_results_by_job_from_sqlite(
    db_path: str,
    *,
    campaign_name: str,
    prefer_corrected: bool = False,
    reverse_bitstring: bool = False,
    only_fetched_ok: bool = True,
) -> Dict[str, List[Dict[str, Any]]]:
    store = CampaignSQLiteStore(db_path)
    rows = store.list_campaign(campaign_name)
    grouped = _group_records_by_job(rows, only_fetched_ok=only_fetched_ok)
    out: Dict[str, List[Dict[str, Any]]] = {}
    for job, (submit_records, fetch_records) in grouped.items():
        out[job] = rb_stitched_results_from_submit_fetch(
            submit_records,
            fetch_records,
            prefer_corrected=prefer_corrected,
            reverse_bitstring=reverse_bitstring,
        )
    return out


def xeb_results_by_depth_from_submit_fetch(
    submit_records: List[Dict[str, Any]],
    fetch_records: List[Tuple[Any, str, Optional[Dict[str, Any]], str]],
    *,
    prefer_corrected: bool = False,
    reverse_bitstring: bool = False,
    depth_key: str = "depth",
) -> Dict[int, List[Tuple[Dict[str, float], Dict[str, Any]]]]:
    """
    Build the structure expected by egm.core.analysis.xeb.analyze_xeb_and_spb_from_results():

        {depth: [(ideal_probs, noisy_counts), ...]}

    Ideal probs are computed by deserializing the stored circuit and running IdealBackend.
    """
    fetch_map: Dict[str, Optional[Dict[str, Any]]] = {str(rid): res for rid, _rt, res, _st in fetch_records}
    ideal_backend = IdealBackend()

    out: Dict[int, List[Tuple[Dict[str, float], Dict[str, Any]]]] = {}
    for rec in submit_records:
        quark_payload = rec.get("quark_payload") or {}
        remote_id = quark_payload.get("remote_id")
        egm_payload = rec.get("egm_payload") or {}
        egm_circuit = egm_payload.get("egm_circuit") or {}
        meta = egm_circuit.get("metadata") or {}
        if not isinstance(meta, Mapping):
            continue
        depth_val = meta.get(depth_key)
        if depth_val is None:
            continue
        depth = int(depth_val)

        circuit = deserialize_circuit(egm_circuit)
        statevector, _ = ideal_backend.run(circuit)
        ideal_probs = ideal_backend.statevector_to_probs(statevector)

        num_qubits = int(egm_circuit.get("num_qubits") or len(egm_circuit.get("qubits") or []))
        raw = fetch_map.get(str(remote_id)) if remote_id is not None else None
        noisy = quark_result_to_counts(
            raw or {},
            num_qubits=num_qubits,
            prefer_corrected=prefer_corrected,
            reverse_bitstring=reverse_bitstring,
        )

        out.setdefault(depth, []).append((ideal_probs, noisy))
    return out


def xeb_results_by_depth_from_datastore_dir(
    datastore_dir: str,
    *,
    prefer_corrected: bool = False,
    reverse_bitstring: bool = False,
    depth_key: str = "depth",
) -> Dict[int, List[Tuple[Dict[str, float], Dict[str, Any]]]]:
    submit_records, fetch_records = load_submit_fetch_from_datastore_dir(datastore_dir)
    return xeb_results_by_depth_from_submit_fetch(
        submit_records,
        fetch_records,
        prefer_corrected=prefer_corrected,
        reverse_bitstring=reverse_bitstring,
        depth_key=depth_key,
    )


def xeb_results_by_depth_from_sqlite(
    db_path: str,
    *,
    campaign_name: Optional[str] = None,
    job_name: Optional[str] = None,
    prefer_corrected: bool = False,
    reverse_bitstring: bool = False,
    depth_key: str = "depth",
    only_fetched_ok: bool = True,
) -> Dict[int, List[Tuple[Dict[str, float], Dict[str, Any]]]]:
    submit_records, fetch_records = load_submit_fetch_from_sqlite(
        db_path,
        campaign_name=campaign_name,
        job_name=job_name,
        only_fetched_ok=only_fetched_ok,
    )
    return xeb_results_by_depth_from_submit_fetch(
        submit_records,
        fetch_records,
        prefer_corrected=prefer_corrected,
        reverse_bitstring=reverse_bitstring,
        depth_key=depth_key,
    )


def xeb_results_by_depth_by_job_from_sqlite(
    db_path: str,
    *,
    campaign_name: str,
    prefer_corrected: bool = False,
    reverse_bitstring: bool = False,
    depth_key: str = "depth",
    only_fetched_ok: bool = True,
) -> Dict[str, Dict[int, List[Tuple[Dict[str, float], Dict[str, Any]]]]]:
    store = CampaignSQLiteStore(db_path)
    rows = store.list_campaign(campaign_name)
    grouped = _group_records_by_job(rows, only_fetched_ok=only_fetched_ok)
    out: Dict[str, Dict[int, List[Tuple[Dict[str, float], Dict[str, Any]]]]] = {}
    for job, (submit_records, fetch_records) in grouped.items():
        out[job] = xeb_results_by_depth_from_submit_fetch(
            submit_records,
            fetch_records,
            prefer_corrected=prefer_corrected,
            reverse_bitstring=reverse_bitstring,
            depth_key=depth_key,
        )
    return out
