from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List, Optional

from egm.datastore.observation_store import ObservationPersistenceDict, ObservationStore


class InMemoryObservationStore(ObservationStore):
    """
    Minimal in-memory implementation of ObservationStore.

    Notes:
    - Stores ObservationPersistenceDict only (no domain objects).
    - Uses deepcopy on save/load to avoid external mutation.
    - No ordering/filtering/aggregation guarantees.
    """

    def __init__(self) -> None:
        self._records: Dict[str, ObservationPersistenceDict] = {}

    def save_observation(self, record: ObservationPersistenceDict) -> str:
        observation_id = uuid.uuid4().hex
        self._records[observation_id] = copy.deepcopy(record)
        return observation_id

    def load_observation(self, observation_id: str) -> Optional[ObservationPersistenceDict]:
        record = self._records.get(observation_id)
        if record is None:
            return None
        return copy.deepcopy(record)

    def list_observation_ids(self) -> List[str]:
        return list(self._records.keys())

    def filter_observations(self, **equals: Any) -> List[ObservationPersistenceDict]:
        """
        Optional helper (not part of ObservationStore contract).

        Supports equality filtering on a small set of common keys:
        task_id / plan_id / protocol / backend_name / chip_name
        """

        allowed = {"task_id", "plan_id", "protocol", "backend_name", "chip_name"}
        unknown = set(equals.keys()) - allowed
        if unknown:
            raise ValueError(f"Unsupported filter keys: {sorted(unknown)}")

        out: List[ObservationPersistenceDict] = []
        for obs_id in self.list_observation_ids():
            rec = self.load_observation(obs_id)
            if rec is None:
                continue
            ok = True
            for k, v in equals.items():
                if rec.get(k) != v:
                    ok = False
                    break
            if ok:
                out.append(rec)
        return out

