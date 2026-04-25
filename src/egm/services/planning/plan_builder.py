"""
services/planning/plan_builder.py

计划实例化与构建器 (Builder)。
"""

import uuid
from typing import Any, Dict, List

from egm.protocols.protocol_factory import ProtocolFactory
from egm.schemas.configs import ConfigSchema
from egm.schemas.plan import CircuitTask, PlanSchema


class PlanBuilder:
    @classmethod
    def generate_circuit_task(
        cls,
        *,
        plan_id: str,
        task_id: str,
        protocol: str,
        qubits: List[int],
        depth: int,
        number_of_circuits: int,
        hardware_meta: Dict[str, Any],
    ) -> CircuitTask:
        """
        [步骤 2] 线路生成：接收单条指令，调用协议底层生成具体的量子线路。
        """

        protocol_obj = ProtocolFactory.create(protocol)
        canonical = getattr(ProtocolFactory, "canonical_protocols", lambda: ())()
        task_kwargs = {
            "qubits": qubits,
            "depths": [depth],
            "number_of_circuits": number_of_circuits,
        }
        if (
            protocol.strip() in {"XEB_ref", "XEB"}
            or "XEB_ref" in canonical
            and protocol.strip() == "XEB_ref"
        ):
            # Compatibility key for XEB-style protocols only.
            task_kwargs["cycles"] = [depth]

        circuits, specific_meta_data = protocol_obj.generate_circuits(task_kwargs)

        reserved_meta_data = hardware_meta.copy()
        reserved_meta_data.update(
            {
                "protocol": protocol,
                "qubits": qubits,
                "depth": depth,
            }
        )
        reserved_keys = set(reserved_meta_data.keys())
        overlap = reserved_keys.intersection(set(specific_meta_data.keys()))
        if overlap:
            raise ValueError(
                f"specific_meta_data must not override reserved meta_data keys: {sorted(overlap)}"
            )
        final_meta_data = reserved_meta_data
        final_meta_data.update(specific_meta_data)
        return CircuitTask(
            plan_id=plan_id,
            task_id=task_id,
            protocol=protocol,
            qubits=qubits,
            number_of_circuits=len(circuits),
            circuits=circuits,
            meta_data=final_meta_data,
        )

    @classmethod
    def pack_tasks_into_plan(cls, tasks: List[CircuitTask]) -> PlanSchema:
        """
        [步骤 3] 装箱打包：基于“单次任务单一后端”的架构前提，直接将所有任务装入唯一的集装箱。
        """

        if not tasks:
            raise ValueError("Cannot build plan: tasks is empty.")

        plan_id = tasks[0].plan_id
        backend = tasks[0].meta_data.get("backend_name", "QPU")

        return PlanSchema(plan_id=plan_id, backend_name=backend, tasks=tasks)

    @classmethod
    def build_plan_from_config(cls, config: ConfigSchema) -> PlanSchema:
        """
        Single planning entrypoint:
        expand ConfigSchema into atomic CircuitTasks and pack into a PlanSchema.
        """

        hardware_meta = {
            "backend_name": config.base.backend_name,
            "chip_name": config.hardware.chip_name,
            "shots": config.protocol.shots,
            "gate_set": config.hardware.gate_set,
            "noise_flags": config.hardware.noise_flags,
        }

        tasks: List[CircuitTask] = []
        for bundle in config.protocol.bundles:
            protocol_name = bundle.protocol
            for qubit_group in bundle.qubits:
                for depth in bundle.depths:
                    task_id = str(uuid.uuid4())
                    tasks.append(
                        cls.generate_circuit_task(
                            plan_id=config.base.plan_id,
                            task_id=task_id,
                            protocol=protocol_name,
                            qubits=qubit_group,
                            depth=depth,
                            number_of_circuits=config.protocol.number_of_circuits,
                            hardware_meta=hardware_meta,
                        )
                    )

        return cls.pack_tasks_into_plan(tasks)

