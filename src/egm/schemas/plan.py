"""
plan.py

定义任务计划结构（PlanSchema）。

语义：
    描述一个“实验执行计划”的组合结构。

作用：
    - Suites 构造 Campaign
    - 描述多实验组合关系
    - 支持批量提交

与 Config 的区别：
    Config = 单个实验的参数
    Plan   = 多个实验的调度与组织

禁止：
    - 不包含执行逻辑
    - 不包含误差语义
"""

"""
plan.py

底层调度执行模块 (Execution Plan Module).
职责:
纯粹的数据载体，作为缺乏业务状态感知（无脑）的物流集装箱，负责打包物理层的发波任务。
彻底剥离所有执行逻辑、状态拉取逻辑和业务分析依赖，仅描述“实验执行计划”的组合结构。
"""

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class CircuitTask:
    """交付给底层调度器的最内层执行单元 (Innermost execution unit for backend scheduler)."""
    plan_id: str
    task_id: str
    protocol: str
    qubits: List[int]
    number_of_circuits: int
    circuits: List[Any]
    meta_data: Dict[str, Any]

@dataclass
class PlanSchema:
    """高度复用的发波集装箱载体 (Highly reusable execution container)."""
    plan_id: str
    backend_name: str
    tasks: List[CircuitTask]
