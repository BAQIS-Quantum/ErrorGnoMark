"""
experiments/protocol_factory.py

实验协议工厂模块。
职责：
提供所有量子实验协议的统一创建入口。
抽象底层协议逻辑，隔离不同实验（如 RB, XEB）的线路生成细节。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

from egm.circuits.circuit import QuantumCircuit

class BaseProtocol(ABC):
    """量子实验协议的抽象基类。强制子类实现标准的线路生成接口。"""
    
    @abstractmethod
    def generate_circuits(self, config: Dict[str, Any]) -> Tuple[List[Any], Dict[str, Any]]:
        """
        生成协议对应的量子线路。
        
        Args:
            config (Dict[str, Any]): 生成线路所需的局部配置字典
            
        Returns:
            Tuple[List[Any], Dict[str, Any]]: (编译后的线路列表, 该协议专属的元数据字典)
        """
        pass

class RBProtocol(BaseProtocol):
    """随机基准测试 (Randomized Benchmarking) 协议实现类"""
    
    def generate_circuits(self, config: Dict[str, Any]) -> Tuple[List[Any], Dict[str, Any]]:
        qubits = config.get("qubits")
        depths = config.get("depths") 
        num_circuits = config.get("number_of_circuits", 1)
        
        # Minimal executable circuit generation (QuantumCircuit list)
        circuits = self._build_rb_circuits(qubits, depths, num_circuits)
        
        # 返回特有的元数据，供后续分析环节使用
        specific_meta_data = {
            "depths": depths,
            "clifford_inverses": ["..."]
        }
        return circuits, specific_meta_data

    def _build_rb_circuits(self, qubits, depths, num_circuits):
        qubits_list = list(qubits or [])
        depths_list = list(depths or [])
        circuits: List[QuantumCircuit] = []
        for d in depths_list:
            for _ in range(int(num_circuits)):
                qc = QuantumCircuit(qubits=qubits_list)
                qc.metadata["depth"] = int(d)
                qc.metadata["protocol"] = "RB"
                circuits.append(qc)
        return circuits


class XEBProtocol(BaseProtocol):
    """交叉熵基准测试 (Cross-Entropy Benchmarking) 协议实现类"""
    
    def generate_circuits(self, config: Dict[str, Any]) -> Tuple[List[Any], Dict[str, Any]]:
        qubits = config.get("qubits")
        # 兼容处理 XEB 中称呼 depth 为 cycles 的习惯
        cycles = config.get("cycles") or config.get("depths") 
        num_circuits = config.get("number_of_circuits", 1)
        
        circuits = self._build_xeb_circuits(qubits, cycles, num_circuits)
        
        specific_meta_data = {
            "cycles": cycles,
            "ideal_probabilities": [0.1, 0.2] 
        }
        return circuits, specific_meta_data
        
    def _build_xeb_circuits(self, qubits, cycles, num_circuits):
        qubits_list = list(qubits or [])
        cycles_list = list(cycles or [])
        circuits: List[QuantumCircuit] = []
        for c in cycles_list:
            for _ in range(int(num_circuits)):
                qc = QuantumCircuit(qubits=qubits_list)
                qc.metadata["depth"] = int(c)
                qc.metadata["protocol"] = "XEB"
                circuits.append(qc)
        return circuits


class ProtocolFactory:
    """协议分发工厂，利用注册表模式管理和实例化具体的实验协议类。"""
    
    # 协议注册表映射
    _registry: Dict[str, type] = {
        "RB_ref": RBProtocol,
        "XEB_ref": XEBProtocol,
    }
    _aliases: Dict[str, str] = {
        "RB": "RB_ref",
        "XEB": "XEB_ref",
    }

    @classmethod
    def canonical_protocols(cls) -> Tuple[str, ...]:
        return tuple(sorted(cls._registry.keys()))

    @classmethod
    def create(cls, protocol_name: str) -> BaseProtocol:
        """根据协议名称字符串实例化相应的协议对象。"""
        if not isinstance(protocol_name, str):
            raise TypeError("protocol_name must be a string.")

        name = protocol_name.strip()
        name = cls._aliases.get(name, name)
        if name not in cls._registry:
            raise ValueError(
                f"Unsupported protocol type: '{protocol_name}'. "
                f"Supported: {list(cls.canonical_protocols())}"
            )
        
        protocol_class = cls._registry[name]
        return protocol_class()
    
    @classmethod
    def register(cls, protocol_name: str, protocol_class: type) -> None:
        """允许在系统运行时动态注册新的自定义协议（开闭原则）。"""
        if not issubclass(protocol_class, BaseProtocol):
            raise TypeError("Registered class must inherit from BaseProtocol.")
        cls._registry[protocol_name] = protocol_class