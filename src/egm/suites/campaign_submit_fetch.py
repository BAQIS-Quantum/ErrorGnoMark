from __future__ import annotations

from typing import Any, Dict, List, Optional

from egm.core.circuits.circuit import QuantumCircuit
from egm.suites.campaign_store_sqlite import CampaignSQLiteStore
from egm.suites.job_submit_fetch import JobSubmitFetch


class CampaignSubmitFetch:
    """
    Campaign layer: submit/fetch across multiple jobs.

    Naming convention:
    - campaign_submit_fetch(): submit all jobs, then fetch all results
    """

    def __init__(self, job: JobSubmitFetch, store: Optional[CampaignSQLiteStore] = None) -> None:
        self.job = job
        self.store = store

    def campaign_submit(
        self,
        experiments: List[Dict[str, Any]],
        shots: int,
        args: Dict[str, Any],
        *,
        campaign_name: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        records: List[Dict[str, Any]] = []
        for exp in experiments:
            job_name = exp.get("name", "job")
            qubits = exp.get("qubits")
            circuits = exp.get("circuits")
            if circuits is None and "experiment" in exp:
                circuits = exp["experiment"].circuits()
            if circuits is None:
                raise ValueError(f"Job '{job_name}' has no circuits.")

            submit_records = self.job.job_submit(
                circuits,
                shots=shots,
                args=args,
                campaign_name=campaign_name or "campaign",
                job_name=job_name,
                campaign_id=campaign_id,
            )
            if self.store is not None:
                self.store.register_submit_records(submit_records)

            records.append(
                {
                    "job_name": job_name,
                    "qubits": qubits,
                    "shots": shots,
                    "submit_records": submit_records,
                }
            )

        return {"campaign": records}

    def campaign_fetch(
        self,
        *,
        campaign_name: str,
        job_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self.store is None:
            raise ValueError("campaign_fetch requires a CampaignSQLiteStore (store=None).")

        submit_records = self.store.get_pending_fetch_submit_records(
            campaign_name=campaign_name,
            job_name=job_name,
        )
        remote_ids = [
            rec.get("quark_payload", {}).get("remote_id")
            for rec in submit_records
            if rec.get("quark_payload", {}).get("remote_id") is not None
        ]
        fetch_records = self.job.job_fetch(remote_ids, submit_records=submit_records)
        self.store.register_fetch_records(fetch_records, submit_records)
        return {"campaign_name": campaign_name, "job_name": job_name, "fetch_records": fetch_records}

    def campaign_submit_fetch(
        self,
        experiments: List[Dict[str, Any]],
        shots: int,
        args: Dict[str, Any],
        *,
        campaign_name: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        submit_out = self.campaign_submit(
            experiments,
            shots,
            args,
            campaign_name=campaign_name,
            campaign_id=campaign_id,
        )
        if self.store is None:
            return submit_out
        name = campaign_name or "campaign"
        fetch_out = self.campaign_fetch(campaign_name=name)
        return {"submit": submit_out, "fetch": fetch_out}

    def run(
        self,
        experiments: List[Dict[str, Any]],
        shots: int,
        args: Dict[str, Any],
        *,
        campaign_name: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.campaign_submit(experiments, shots, args, campaign_name=campaign_name, campaign_id=campaign_id)

    @staticmethod
    def as_experiment(
        name: str,
        experiment: Any,
        qubits: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        return {"name": name, "experiment": experiment, "qubits": qubits}

    @staticmethod
    def as_circuits(
        name: str,
        circuits: List[QuantumCircuit],
        qubits: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        return {"name": name, "circuits": circuits, "qubits": qubits}
