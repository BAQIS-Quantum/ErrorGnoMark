"""
semantics/plan_builder.py

计划实例化与构建器 (Builder)。
"""

from dataclasses import dataclass
from typing import List, Dict, Any

from egm.experiments.protocol_factory import ProtocolFactory
from egm.schemas.plan import CircuitTask, PlanSchema

@dataclass
class TaskInstruction:
    plan_id: str
    task_id: str
    protocol: str
    qubits: List[int]
    depth: List[int]
    number_of_circuits: int
    hardware_meta: Dict[str, Any]

class PlanBuilder:
    
    @classmethod
    def generate_circuit_task(cls, inst: TaskInstruction) -> CircuitTask:
        """
        [步骤 2] 线路生成：接收单条指令，调用协议底层生成具体的量子线路。
        """
        protocol_obj = ProtocolFactory.create(inst.protocol)
        task_kwargs = {
            "qubits": inst.qubits, "depths": inst.depth,
            "cycles": inst.depth, "number_of_circuits": inst.number_of_circuits
        }
        
        circuits, specific_meta_data = protocol_obj.generate_circuits(task_kwargs)
        
        final_meta_data = inst.hardware_meta.copy()
        final_meta_data.update({
            "protocol": inst.protocol,
            "qubits": inst.qubits,
            **specific_meta_data
        })
        
    @classmethod
    def generate_tasks_batch(cls, instructions: List[TaskInstruction]) -> List[CircuitTask]:
        """
        批量线路生成：接收指令列表，自动循环生成所有任务。
        利用列表推导式让代码更Pythonic。
        """
        return [cls.generate_circuit_task(inst) for inst in instructions]
        
        return CircuitTask(
            plan_id=inst.plan_id, task_id=inst.task_id, protocol=inst.protocol,
            qubits=inst.qubits, number_of_circuits=len(circuits),
            circuits=circuits, meta_data=final_meta_data
        )

    @classmethod
    def pack_tasks_into_plan(cls, tasks: List[CircuitTask]) -> PlanSchema:
        """
        [步骤 3] 装箱打包：基于“单次任务单一后端”的架构前提，直接将所有任务装入唯一的集装箱。
        """
        if not tasks:
            return PlanSchema(plan_id="Empty", backend_name="QPU", tasks=[])
            
        # 因为系统保证了每次任务 plan_id 和 backend 的唯一性，
        # 直接从第一个包裹中提取这两个宏观属性作为集装箱的标签即可。
        plan_id = tasks[0].plan_id
        backend = tasks[0].meta_data.get("backend", "QPU")
        
        return PlanSchema(
            plan_id=plan_id, 
            backend_name=backend, 
            tasks=tasks  # 直接塞入全部包裹
        )
        
    @classmethod
    def build_plan(cls, instructions: List[TaskInstruction]) -> PlanSchema:
        """
        一键装配流水线：向外部彻底隐藏“生成子任务”和“装箱”的过程。
        输入指令列表，直接吐出最终的 Plan 集装箱。
        """
        tasks = cls.generate_tasks_batch(instructions)
        return cls.pack_tasks_into_plan(tasks)