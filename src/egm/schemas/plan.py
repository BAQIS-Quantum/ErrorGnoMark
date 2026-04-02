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


from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ExperimentConfig(BaseModel):

    # ===== 1. 基本信息 =====
    id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0"

    # ===== 2. 实验类型 =====
    experiment_type: str
    # 例如:
    # "single_qubit_rb"
    # "two_qubit_rb"
    # "crosstalk"
    # "channel_spectrum"
    # "entanglement"

    # ===== 3. 目标平台 =====
    backend: str
    # 例如:
    # "baqis_qpu_v1"
    # "ibmq_backend"
    # "local_simulator"

    target_qubits: List[int]

    # ===== 4. 实验参数 =====
    parameters: Dict[str, Any]
    # 例如:
    # {
    #     "num_cliffords": 100,
    #     "num_samples": 30,
    #     "depth_range": [1, 50],
    # }

    # ===== 5. 执行控制参数 =====
    shots: int = 1024
    repetitions: int = 1
    seed: Optional[int] = None
    parallel: bool = False

    # ===== 6. 输出与报告控制 =====
    save_raw_data: bool = True
    generate_report: bool = True
    report_format: str = "json"  # or "pdf"