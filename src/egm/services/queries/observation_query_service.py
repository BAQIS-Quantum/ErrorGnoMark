from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from egm.datastore.observation_store import ObservationPersistenceDict, ObservationStore


@dataclass(frozen=True)
class ObservationQueryService:
    store: ObservationStore

    def get_observation(self, observation_id: str) -> Optional[ObservationPersistenceDict]:
        return self.store.load_observation(observation_id)

    def list_observations(self) -> list[ObservationPersistenceDict]:
        out: list[ObservationPersistenceDict] = []
        for obs_id in self.store.list_observation_ids():
            rec = self.store.load_observation(obs_id)
            if rec is not None:
                out.append(rec)
        return out

    def filter_observations(
        self,
        *,
        task_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        protocol: Optional[str] = None,
        backend_name: Optional[str] = None,
        chip_name: Optional[str] = None,
    ) -> list[ObservationPersistenceDict]:
        filters = {
            "task_id": task_id,
            "plan_id": plan_id,
            "protocol": protocol,
            "backend_name": backend_name,
            "chip_name": chip_name,
        }
        active = {k: v for k, v in filters.items() if v is not None}

        if not active:
            return self.list_observations()

        out: list[ObservationPersistenceDict] = []
        for rec in self.list_observations():
            ok = True
            for k, v in active.items():
                if rec.get(k) != v:
                    ok = False
                    break
            if ok:
                out.append(rec)
        return out

