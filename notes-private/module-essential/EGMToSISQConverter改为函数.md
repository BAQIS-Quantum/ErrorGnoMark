### EGMToSISQConverter改为函数

当前类的唯一实例变量是 `self.qubit_mapping`，但它在每次 `convert()` 调用时都会被重新创建（第44行）。这意味着**类没有任何需要跨调用保持的状态**，完全可以改为纯函数。

#### 重构方案

```python
"""
ErrorGnoMark 到 SISQ 转换器

实现从 ErrorGnoMark 的 QuantumCircuit 到 SISQ 的 QiProgram 的转换。
"""

from typing import Dict, List, Optional
import numpy as np
from pyquiet.qir.qi_prog import QiProgram
from pyquiet.qir.qvariable import NonListVariable, QuietType, PhyQubit
from pyquiet.qir.structure import Function, FuncBody, VarDecl, FuncCall, Module
from pyquiet.qir.qinstructions.modules_instruction.gm import *
from pyquiet.qir.qlayout.interface import QubitDeclaration


def egm_to_sisq(
    egm_circuit,
    file_name: str = "converted.sisq",
    qubit_name_map: Optional[Dict[int, str]] = None,
) -> QiProgram:
    """
    将 ErrorGnoMark 的 QuantumCircuit 转换为 SISQ 的 QiProgram。

    Args:
        egm_circuit: ErrorGnoMark 的 QuantumCircuit 对象
        file_name: 输出文件名
        qubit_name_map: 可选的逻辑比特到物理比特名的映射，
                       如 {0: 'q5', 1: 'q6'}。
                       若不提供则默认映射为 q0, q1, ...

    Returns:
        QiProgram: 转换后的 SISQ 程序
    """
    # 创建量子比特映射
    if qubit_name_map is not None:
        qubit_mapping = {i: qubit_name_map[i] for i in egm_circuit.qubits}
    else:
        qubit_mapping = {i: f"q{i}" for i in egm_circuit.qubits}

    # 1. 创建 QiProgram
    qi_program = QiProgram(file_name)

    # 2. 设置模块依赖
    qi_program.load_module_set(Module.gm)

    # 3. 生成layout段
    _generate_layout_section(qi_program, egm_circuit.qubits, qubit_mapping)

    # 4. 转换门操作到.code段
    _convert_gates(qi_program, egm_circuit, qubit_mapping)

    # 5. 生成入口段
    _generate_entry_section(qi_program)

    return qi_program


def _generate_layout_section(
    qi_program: QiProgram, 
    qubits: List[int], 
    qubit_mapping: Dict[int, str]
):
    """生成layout段，声明物理量子比特"""
    phy_qubits = [PhyQubit(qubit_mapping[i]) for i in qubits]
    if phy_qubits:
        qubit_decl = QubitDeclaration(phy_qubits)
        qi_program.add_layout_qubit_decl(qubit_decl)


def _convert_gates(
    qi_program: QiProgram, 
    egm_circuit, 
    qubit_mapping: Dict[int, str]
):
    """转换量子门操作到.code段"""
    func_body = FuncBody()

    # 插入reset指令
    phy_qubit_vars = [PhyQubit(qubit_mapping[i]) for i in egm_circuit.qubits]
    if phy_qubit_vars:
        func_body.add_instruction(FuncCall("reset", phy_qubit_vars, []))

    # 收集测量操作，转换其他门
    measured_qubits = []
    for gate in egm_circuit.gates:
        if gate.name == "measure":
            measured_qubits.append(gate.qubits[0])
        else:
            instruction = _gate_to_instruction(gate, qubit_mapping)
            func_body.add_instruction(instruction)

    # 生成合并的measure调用
    if measured_qubits:
        measure_vars = [PhyQubit(qubit_mapping[q]) for q in measured_qubits]
        func_body.add_instruction(FuncCall("measure", measure_vars, []))

    # 构造 Function
    function = Function()
    function.init_name("quantum_circuit")
    function.init_input_args([])
    function.init_output_args([])
    for instruction in func_body.instructions:
        function.push_instr(instruction)

    qi_program.add_define_function(function)


def _gate_to_instruction(gate, qubit_mapping: Dict[int, str]):
    """将单个门转换为 SISQ 指令"""
    gate_name = gate.name.lower()
    
    # 辅助函数：获取物理量子比特
    def q(idx: int) -> PhyQubit:
        return PhyQubit(qubit_mapping[gate.qubits[idx]])

    # === 1. 基础单量子比特门 ===
    if gate_name in ["i", "id"]:
        return I(q(0))
    elif gate_name == "h":
        return H(q(0))
    elif gate_name == "x":
        return X(q(0))
    elif gate_name == "y":
        return Y(q(0))
    elif gate_name == "z":
        return Z(q(0))
    elif gate_name == "s":
        return S(q(0))
    elif gate_name == "sdg":
        return Sdag(q(0))
    elif gate_name == "t":
        return T(q(0))
    elif gate_name == "tdg":
        return Tdag(q(0))

    # === 2. 物理门（EGM 特有） ===
    elif gate_name in ["sx", "sqrtx", "sqrt_x"]:
        return Sx(q(0))
    elif gate_name in ["sy", "sqrty", "sqrt_y"]:
        return Sy(q(0))
    elif gate_name == "rx90":
        return Rx(q(0), [np.pi / 2])
    elif gate_name in ["rxm90", "sxdg"]:
        return Rx(q(0), [-np.pi / 2])
    elif gate_name == "ry90":
        return Ry(q(0), [np.pi / 2])
    elif gate_name == "rym90":
        return Ry(q(0), [-np.pi / 2])

    # === 3. 参数化门 ===
    elif gate_name == "rx" and gate.params:
        return Rx(q(0), list(gate.params))
    elif gate_name == "ry" and gate.params:
        return Ry(q(0), list(gate.params))
    elif gate_name == "rz" and gate.params:
        return Rz(q(0), list(gate.params))
    elif gate_name == "u1" and gate.params:
        return U1(q(0), list(gate.params))
    elif gate_name == "u2" and gate.params:
        return U2(q(0), list(gate.params))
    elif gate_name in ["u3", "u"] and gate.params:
        return U3(q(0), list(gate.params))

    # === 4. 双量子比特门 ===
    elif gate_name in ["cnot", "cx"]:
        return CNOT(q(0), q(1))
    elif gate_name == "cz":
        return CZ(q(0), q(1))
    elif gate_name == "swap":
        return SWAP(q(0), q(1))
    elif gate_name == "iswap":
        return ISwap(q(0), q(1))
    elif gate_name == "ecr":
        return ECR(q(0), q(1))

    # === 5. 三量子比特门 ===
    elif gate_name in ["ccnot", "toffoli"]:
        return Toffoli(q(0), q(1), q(2))
    elif gate_name in ["cswap", "fredkin"]:
        return Fredkin(q(0), q(1), q(2))
    elif gate_name == "ccz":
        return CCZ(q(0), q(1), q(2))
    else:
        raise ValueError(f"不支持的门类型: {gate.name}")


def _generate_entry_section(qi_program: QiProgram):
    """生成入口段代码"""
    qi_program.add_entry_instruction(FuncCall("quantum_circuit", [], []))


# 保持向后兼容的类包装器
class EGMToSISQConverter:
    """[已废弃] 请直接使用 egm_to_sisq() 函数"""
    
    def convert(
        self, 
        egm_circuit, 
        file_name: str = "converted.sisq",
        qubit_name_map: Optional[Dict[int, str]] = None,
    ) -> QiProgram:
        return egm_to_sisq(egm_circuit, file_name, qubit_name_map)
```

#### 改进点

| 方面 | 改进 |
|------|------|
| **更简洁的调用** | `egm_to_sisq(circuit)` vs `EGMToSISQConverter().convert(circuit)` |
| **新增 `qubit_name_map` 参数** | 直接在转换时完成物理比特映射，消除 QuantaCS 中的字符串替换 |
| **代码更紧凑** | `_gate_to_instruction` 使用辅助函数 `q()` 减少重复 |
| **向后兼容** | 保留类包装器，现有代码无需修改 |

#### QuantaCS 调用方式对比

**之前：**
```python
converter = EGMToSISQConverter()
sisq_program = converter.convert(logical_circuit, "test.sisq")
qubit_dict = {i: qubits[i] for i in range(len(qubits))}
mapped_sisq_str = self._replace_qubit_name(str(sisq_program), qubit_dict)
mapped_program = QiParser().parse(mapped_sisq_str, is_string_content=True)
```

**之后：**
```python
qubit_name_map = {i: qubits[i] for i in range(len(qubits))}
sisq_program = egm_to_sisq(logical_circuit, "test.sisq", qubit_name_map)
# 无需字符串替换和重新解析！
```

#### 结论

✅ **完全可行且推荐**，因为：
1. 当前类没有任何需要跨调用保持的状态
2. 纯函数更符合这种"输入→转换→输出"的场景
3. 顺便解决了 QuantaCS 中的字符串级别比特映射问题

![[EGM中顶层实验类的必要性讨论]]

### EGMToSISQConverter改为函数

当前类的唯一实例变量是 `self.qubit_mapping`，但它在每次 `convert()` 调用时都会被重新创建（第44行）。这意味着**类没有任何需要跨调用保持的状态**，完全可以改为纯函数。

#### 重构方案

```python
"""
ErrorGnoMark 到 SISQ 转换器

实现从 ErrorGnoMark 的 QuantumCircuit 到 SISQ 的 QiProgram 的转换。
"""

from typing import Dict, List, Optional
import numpy as np
from pyquiet.qir.qi_prog import QiProgram
from pyquiet.qir.qvariable import NonListVariable, QuietType, PhyQubit
from pyquiet.qir.structure import Function, FuncBody, VarDecl, FuncCall, Module
from pyquiet.qir.qinstructions.modules_instruction.gm import *
from pyquiet.qir.qlayout.interface import QubitDeclaration


def egm_to_sisq(
    egm_circuit,
    file_name: str = "converted.sisq",
    qubit_name_map: Optional[Dict[int, str]] = None,
) -> QiProgram:
    """
    将 ErrorGnoMark 的 QuantumCircuit 转换为 SISQ 的 QiProgram。

    Args:
        egm_circuit: ErrorGnoMark 的 QuantumCircuit 对象
        file_name: 输出文件名
        qubit_name_map: 可选的逻辑比特到物理比特名的映射，
                       如 {0: 'q5', 1: 'q6'}。
                       若不提供则默认映射为 q0, q1, ...

    Returns:
        QiProgram: 转换后的 SISQ 程序
    """
    # 创建量子比特映射
    if qubit_name_map is not None:
        qubit_mapping = {i: qubit_name_map[i] for i in egm_circuit.qubits}
    else:
        qubit_mapping = {i: f"q{i}" for i in egm_circuit.qubits}

    # 1. 创建 QiProgram
    qi_program = QiProgram(file_name)

    # 2. 设置模块依赖
    qi_program.load_module_set(Module.gm)

    # 3. 生成layout段
    _generate_layout_section(qi_program, egm_circuit.qubits, qubit_mapping)

    # 4. 转换门操作到.code段
    _convert_gates(qi_program, egm_circuit, qubit_mapping)

    # 5. 生成入口段
    _generate_entry_section(qi_program)

    return qi_program


def _generate_layout_section(
    qi_program: QiProgram, 
    qubits: List[int], 
    qubit_mapping: Dict[int, str]
):
    """生成layout段，声明物理量子比特"""
    phy_qubits = [PhyQubit(qubit_mapping[i]) for i in qubits]
    if phy_qubits:
        qubit_decl = QubitDeclaration(phy_qubits)
        qi_program.add_layout_qubit_decl(qubit_decl)


def _convert_gates(
    qi_program: QiProgram, 
    egm_circuit, 
    qubit_mapping: Dict[int, str]
):
    """转换量子门操作到.code段"""
    func_body = FuncBody()

    # 插入reset指令
    phy_qubit_vars = [PhyQubit(qubit_mapping[i]) for i in egm_circuit.qubits]
    if phy_qubit_vars:
        func_body.add_instruction(FuncCall("reset", phy_qubit_vars, []))

    # 收集测量操作，转换其他门
    measured_qubits = []
    for gate in egm_circuit.gates:
        if gate.name == "measure":
            measured_qubits.append(gate.qubits[0])
        else:
            instruction = _gate_to_instruction(gate, qubit_mapping)
            func_body.add_instruction(instruction)

    # 生成合并的measure调用
    if measured_qubits:
        measure_vars = [PhyQubit(qubit_mapping[q]) for q in measured_qubits]
        func_body.add_instruction(FuncCall("measure", measure_vars, []))

    # 构造 Function
    function = Function()
    function.init_name("quantum_circuit")
    function.init_input_args([])
    function.init_output_args([])
    for instruction in func_body.instructions:
        function.push_instr(instruction)

    qi_program.add_define_function(function)


def _gate_to_instruction(gate, qubit_mapping: Dict[int, str]):
    """将单个门转换为 SISQ 指令"""
    gate_name = gate.name.lower()
    
    # 辅助函数：获取物理量子比特
    def q(idx: int) -> PhyQubit:
        return PhyQubit(qubit_mapping[gate.qubits[idx]])

    # === 1. 基础单量子比特门 ===
    if gate_name in ["i", "id"]:
        return I(q(0))
    elif gate_name == "h":
        return H(q(0))
    elif gate_name == "x":
        return X(q(0))
    elif gate_name == "y":
        return Y(q(0))
    elif gate_name == "z":
        return Z(q(0))
    elif gate_name == "s":
        return S(q(0))
    elif gate_name == "sdg":
        return Sdag(q(0))
    elif gate_name == "t":
        return T(q(0))
    elif gate_name == "tdg":
        return Tdag(q(0))

    # === 2. 物理门（EGM 特有） ===
    elif gate_name in ["sx", "sqrtx", "sqrt_x"]:
        return Sx(q(0))
    elif gate_name in ["sy", "sqrty", "sqrt_y"]:
        return Sy(q(0))
    elif gate_name == "rx90":
        return Rx(q(0), [np.pi / 2])
    elif gate_name in ["rxm90", "sxdg"]:
        return Rx(q(0), [-np.pi / 2])
    elif gate_name == "ry90":
        return Ry(q(0), [np.pi / 2])
    elif gate_name == "rym90":
        return Ry(q(0), [-np.pi / 2])

    # === 3. 参数化门 ===
    elif gate_name == "rx" and gate.params:
        return Rx(q(0), list(gate.params))
    elif gate_name == "ry" and gate.params:
        return Ry(q(0), list(gate.params))
    elif gate_name == "rz" and gate.params:
        return Rz(q(0), list(gate.params))
    elif gate_name == "u1" and gate.params:
        return U1(q(0), list(gate.params))
    elif gate_name == "u2" and gate.params:
        return U2(q(0), list(gate.params))
    elif gate_name in ["u3", "u"] and gate.params:
        return U3(q(0), list(gate.params))

    # === 4. 双量子比特门 ===
    elif gate_name in ["cnot", "cx"]:
        return CNOT(q(0), q(1))
    elif gate_name == "cz":
        return CZ(q(0), q(1))
    elif gate_name == "swap":
        return SWAP(q(0), q(1))
    elif gate_name == "iswap":
        return ISwap(q(0), q(1))
    elif gate_name == "ecr":
        return ECR(q(0), q(1))

    # === 5. 三量子比特门 ===
    elif gate_name in ["ccnot", "toffoli"]:
        return Toffoli(q(0), q(1), q(2))
    elif gate_name in ["cswap", "fredkin"]:
        return Fredkin(q(0), q(1), q(2))
    elif gate_name == "ccz":
        return CCZ(q(0), q(1), q(2))
    else:
        raise ValueError(f"不支持的门类型: {gate.name}")


def _generate_entry_section(qi_program: QiProgram):
    """生成入口段代码"""
    qi_program.add_entry_instruction(FuncCall("quantum_circuit", [], []))


# 保持向后兼容的类包装器
class EGMToSISQConverter:
    """[已废弃] 请直接使用 egm_to_sisq() 函数"""
    
    def convert(
        self, 
        egm_circuit, 
        file_name: str = "converted.sisq",
        qubit_name_map: Optional[Dict[int, str]] = None,
    ) -> QiProgram:
        return egm_to_sisq(egm_circuit, file_name, qubit_name_map)
```

#### 改进点

| 方面 | 改进 |
|------|------|
| **更简洁的调用** | `egm_to_sisq(circuit)` vs `EGMToSISQConverter().convert(circuit)` |
| **新增 `qubit_name_map` 参数** | 直接在转换时完成物理比特映射，消除 QuantaCS 中的字符串替换 |
| **代码更紧凑** | `_gate_to_instruction` 使用辅助函数 `q()` 减少重复 |
| **向后兼容** | 保留类包装器，现有代码无需修改 |

#### QuantaCS 调用方式对比

**之前：**
```python
converter = EGMToSISQConverter()
sisq_program = converter.convert(logical_circuit, "test.sisq")
qubit_dict = {i: qubits[i] for i in range(len(qubits))}
mapped_sisq_str = self._replace_qubit_name(str(sisq_program), qubit_dict)
mapped_program = QiParser().parse(mapped_sisq_str, is_string_content=True)
```

**之后：**
```python
qubit_name_map = {i: qubits[i] for i in range(len(qubits))}
sisq_program = egm_to_sisq(logical_circuit, "test.sisq", qubit_name_map)
# 无需字符串替换和重新解析！
```

#### 结论

✅ **完全可行且推荐**，因为：
1. 当前类没有任何需要跨调用保持的状态
2. 纯函数更符合这种"输入→转换→输出"的场景
3. 顺便解决了 QuantaCS 中的字符串级别比特映射问题
