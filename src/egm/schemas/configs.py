"""
configs.py

定义实验配置结构（Experiment Configuration Schema）。

语义：
    描述“要做什么实验”，
    不描述“实验如何执行”。

作用：
    - Experiments 的输入
    - Suites 构造实验时使用
    - execution 层调度参数来源

内容示例：
    - backend_name
    - shots
    - qubits
    - gate_set
    - noise_flags

注意：
    ConfigSchema 只描述参数，不包含执行结果。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ConfigBase:
    plan_id: str
    backend_name: str


@dataclass(frozen=True)
class HardwareConfig:
    chip_name: str
    gate_set: str
    noise_flags: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProtocolBundle:
    """
    One bundle describes one protocol family applied to multiple qubit-groups,
    across multiple depths.
    """

    protocol: str
    qubits: List[List[int]]
    depths: List[int]


@dataclass(frozen=True)
class ProtocolConfig:
    number_of_circuits: int
    shots: int
    bundles: List[ProtocolBundle] = field(default_factory=list)


@dataclass(frozen=True)
class ConfigSchema:
    base: ConfigBase
    hardware: HardwareConfig
    protocol: ProtocolConfig

    # Optional extension hook (intentionally untyped for now)
    extra: Optional[Dict[str, Any]] = None