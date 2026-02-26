## 1 目标

将 `EGM` 中的 `QuantumCircuit` 类的底层表示替换为 `sisq-parser` 中的 `SISQProgram`。

## 2 SISQ 简介

目前EGM中使用到的SISQ程序有如下特点：
- 仅使用线路层指令（`using gm`）
- 只有一个函数(`.code 段中的 quantum_circuit()`)
- 使用的 `qubit` 均为芯片上实际存在的 `physical qubit`

与EGM QuantumCircuit的差异：
- `qubit` 不是默认状态为 $\ket{0}$，需通过`reset()` 将比特显式置为 $\ket{0}$
- `measure()` 可能存在多路测量的情况，即同时测量多个`qubit`（如`measure($aq10, $aq11)`）
- `qubit`名称为 `$+str` 的字符串格式，区别于`QuantumCircuit` 中 `int` 类型的 `qubit index` 表示

以`RB`实验为例：
```
//Creating RBExperiment...
//[INFO] RB Experiment initialized (2Q, x_axis=GATE_COUNT, native=ON).
//SUCCESS: Generated a total of 1 circuits for depths [1].
//Generated 1 SISQ programs
using gm
.gate:
.pulse:
.code:
		def_func quantum_circuit():
				reset($aq10, $aq11)
				Rz(-1.570796) $aq10
				Sx $aq10
				Rz(1.570796) $aq10
				Sx $aq10
				Rz(-1.570796) $aq10
				X $aq11
				Rz(1.570796) $aq11
				Sx $aq11
				Rz(1.570796) $aq11
				Sx $aq11
				CZ $aq10, $aq11
				Sx $aq11
				Rz(1.570796) $aq11
				Sx $aq11
				X $aq10
				Y $aq11
				Rz(1.570796) $aq11
				Rz(-1.570796) $aq11
				Y $aq11
				X $aq10
				Sx $aq11
				Rz(1.570796) $aq11
				Sx $aq11
				CZ $aq10, $aq11
				Sx $aq11
				Rz(1.570796) $aq11
				Sx $aq11
				Rz(-1.570796) $aq11
				X $aq11
				Rz(1.570796) $aq10
				Sx $aq10
				Rz(1.570796) $aq10
				Sx $aq10
				Rz(1.570796) $aq10
				measure($aq10, $aq11)
		end
.entry:
		quantum_circuit()
.layout:
		qubit $aq10
		qubit $aq11

```

### 3 QuantaCS 中对于EGM的使用

### 3.1 线路生成

```python
# QuantaCS/src/quanta_cs/experiment/sisq_experiment/benchmarking_experiment.py

self.bulk_exp = StandardRBExperiment(
		qubits=[int(i) for i in range(len(qubits))],
		depths=bulk_depths,
		circuits_per_depth=circs_per_depth,
		native_gates=list(CUSTOM_NATIVE_GATES.keys()),
		x_axis_mode=self.x_axis_mode,
		seed=self.seed,
)

all_circuits = self.bulk_exp.circuits()
```

期望的改进（这种代码重构的问题也可暂时先不考虑）：
如果 `EGM` 能够提供`gen_rb_circuits()` 方法，即将`StandardRBExperiment` 拆分为多个功能函数
代码可进一步简化：

```python
all_circuits = gen_rb_circuits(
		qubits=[int(i) for i in range(len(qubits))],
		depths=bulk_depths,
		circuits_per_depth=circs_per_depth,
		native_gates=list(CUSTOM_NATIVE_GATES.keys()),
		x_axis_mode=self.x_axis_mode,
		seed=self.seed,
)
```
### 3.2 模拟与数据处理

```python
from errorgnomark.engine import QuantumEngine
from errorgnomark.backends.dummy_backend_xeb import DummyBackend
backend = DummyBackend(cycle_fidelity=1, spam_error=0.0005)
engine = QuantumEngine(backend)
Exp.bulk_exp.run(engine=engine, shots=2**10, experimental_results=user_data, plot=True,circuits=Exp.bulk_exp.circuits())
```

其中 `user_data` 为QuantaCS用户在真机上运行线路（如`rb`）后的测量结果数据，结构如下：
```
[{'00': 0.6569408054254819,
  '01': 0.2612284417047437,
  '10': 0.06270423167725045,
  '11': 0.01912652336903129},
 {'00': 0.15766739354354403,
  '01': 0.15293030277723985,
  '10': 0.35063246081442545,
  '11': 0.33876984427546764},
 {'00': 0.2409476160174294,
  '01': 0.09349923883533269,
  '10': 0.4547811500669247,
  '11': 0.21077199357521417},
 {'00': 0.16526493891513916,
  '01': 0.16498717774272517,
  '10': 0.3401630456798129,
  '11': 0.3295848392064125},
 {'00': 0.21018544851024695,
  '01': 0.257590164617552,
  '10': 0.26291853569600704,
  '11': 0.2693058538159689},
  ...
```



## 4 阶段一：EGM中实现 `to_sisq` 方法

**目标**：将转换逻辑从 `sisq-parser` 移入 `ErrorGnoMark`，使 `QuantumCircuit` 具备自我转换能力。这既是功能增强，也是为第二阶段重构建立 "Ground Truth"（基准真值）。

### 5.1 添加依赖
在 `ErrorGnoMark` 的 `pyproject.toml` 或 `setup.py` 中添加对 `sisq` 的依赖。

### 5.2 实现 `to_sisq` 方法
在 `errorgnomark/circuits/circuit.py` 中，修改 `QuantumCircuit` 类，移植 `egm_to_sisq.py` 的逻辑。

**代码修改示例：**

```python
# errorgnomark/circuits/circuit.py

from sisq.ast.program import SISQProgram
from sisq.ast.variable import PhyQubit
from sisq.ast import Function, FuncBody, FuncCall, Module
# 导入所有门定义...
from sisq.ast.modules.gate import H, CNOT, Rx, Ry, Rz, Measure  # 举例

class QuantumCircuit:
    def __init__(self, qubits):
        self.qubits = qubits
        self.gates = []  # 目前仍保留此列表
    
    # ... 原有的 add_gate 等方法保持不变 ...

    def to_sisq(self, file_name: str = "converted.sisq", qubit_list) -> SISQProgram:
        """
        将当前 QuantumCircuit 转换为 SISQProgram 对象。
        逻辑源自原 sisq-parser/python/src/sisq/converter/egm_to_sisq.py
        """
        ...
        
        return qi_program
```


### 5.3 其他修改建议

1. 对于 `StandardRBExperiment`的`_generate_circuit()`方法
	- 添加`with_reset`参数：是否添加`reset`
	- 添加`qubit_list`参数，类型为`LIST[str]`：用于`qubit index` 与 `physical qubit name` 的转换
	- 添加`with_measure`参数：是否在门序列后生成`measure`操作
2. 对于`QuantumCircuit` 的 `measure_all()`
	- 添加`is_multi_readout`：表示是否需要同时测量


---

## 5 阶段二：底层替换 (Replacement) - 重写 QuantumCircuit 属性和方法

**核心思想**：
- `QuantumCircuit` 直接继承 `SISQProgram`，完全基于 SISQ 的内部结构
- 不再使用 EGM 的 Gate 类，直接使用 SISQ 的 Gate 类（如 `sisq.ast.modules.gate.H`, `CNOT` 等）
- `QuantumCircuit` 不再维护独立的门列表，所有门操作都存储在 SISQ 的 `quantum_circuit` 函数中
- 通过属性访问器提供兼容接口，但底层数据完全来自 SISQ

**重要变更**：
- 这是一个破坏性变更：`add_gate()` 现在接受 SISQ Gate 对象，而不是 EGM Gate 对象
- `gates` 属性返回 SISQ Gate 对象列表，而不是 EGM Gate 对象列表
- 需要迁移现有代码，将 EGM Gate 替换为对应的 SISQ Gate

#### 5.1 重写核心属性
直接使用 SISQ 的内部结构，不再维护 EGM Gate 列表。

```python
# 旧
class QuantumCircuit:
	def __init__(self, qubits: List[int], gates: Optional[List[Gate]] = None):
			self.qubits = sorted(set(qubits))
			self.gates: List[Gate] = gates[:] if gates else []
			self.num_qubits = len(self.qubits)
			self.metadata: Dict[str, Any] = {}   
```

```python
# 新
class QuantumCircuit(SISQProgram):
	def __init__(self, qubits: List[int], gates: Optional[List[Gate]] = None):
			self.metadata: Dict[str, Any] = {} 
				
  @property 
	def qubits(self) -> List[PhyQubit]:
			""" 获取layout段中声明的phy_qubits """
			pass
	    
	@property
	def gates(self) -> List[Gate]
		""" 获取code段中quantum_circuit函数中的所有门操作 """
			pass
	
	@property
	def num_qubits(self) -> int
		return len(self.qubits)
	  
```

#### 5.2 重写核心方法
将 EGM 的 `Gate` 对象即时“编译”为 SISQ 指令。

```python

# 旧
def add_gate(self, g: Gate): self.gates.append(g)
def add_gates(self, gs: List[Gate]): self.gates.extend(gs)

# 新
def add_gate(self, g: Gate): # 注：这里的Gate是SISQ中的类
	"""将Gate指令添加到code段的quantum_circuit函数中"""


# 补齐剩下的方法
```

更多详细实现见[7 详细实现](## 7 详细实现)

---

## 6 阶段三：验证与测试策略 (Verification)

### 6.1 线路生成测试
- 阶段一实验生成的SISQ程序作为基准
- 只需确保阶段二生成的SISQ程序与基准一致


### 6.2 RB 实验回归测试
在 `tests/test_experiments_rb.py` 中运行 `StandardRBExperiment`。
*   **验证点**: 
    *   电路生成不报错。
    *   `decompose` 后生成的 SISQ 程序仅包含指定的 `native_gates`。
    *   `gate_count` 统计正确。

---



## 7 详细实现

#### 7.1 重写核心属性
直接使用 SISQ 的内部结构，不再维护 EGM Gate 列表。

```python
# 旧实现（EGM Gate）
class QuantumCircuit:
	def __init__(self, qubits: List[int], gates: Optional[List[Gate]] = None):
		self.qubits = sorted(set(qubits))
		self.gates: List[Gate] = gates[:] if gates else []  # EGM Gate 列表
		self.num_qubits = len(self.qubits)
		self.metadata: Dict[str, Any] = {}   
```

```python
# 新实现（直接使用 SISQ）
from sisq.ast.program import SISQProgram
from sisq.ast.variable import PhyQubit
from sisq.ast import Function, FuncCall, Module
from sisq.ast.layout_elements import QubitDeclaration
from typing import List, Optional, Dict, Union

class QuantumCircuit(SISQProgram):
	"""基于 SISQProgram 的量子电路实现"""
	
	# 常量：默认的 quantum_circuit 函数名
	QUANTUM_CIRCUIT_FUNC_NAME = "quantum_circuit"
	
	def __init__(
		self, 
		qubits: List[int], 
		gates: Optional[List] = None,  # 现在是 SISQ Gate 列表
		qubit_name_map: Optional[Dict[int, str]] = None,
		with_reset: bool = True
	):
		"""
		初始化 QuantumCircuit。
		
		Args:
			qubits: EGM 风格的 qubit index 列表（int 类型）
			gates: 可选的 SISQ Gate 对象列表
			qubit_name_map: 可选的 qubit index 到物理 qubit 名称的映射
			with_reset: 是否在函数开头添加 reset 操作
		"""
		if not qubits:
			raise ValueError("QuantumCircuit 必须至少有一个 qubit")
		
		# 调用父类初始化
		super().__init__(file_name="circuit.sisq")
		
		# 保存元数据
		self.metadata: Dict[str, Any] = {}
		
		# 建立 qubit index 到名称的映射
		if qubit_name_map is not None:
			self._qubit_index_to_name = {
				q: qubit_name_map[q] for q in sorted(set(qubits))
			}
		else:
			# 默认映射：0 -> "aq0", 1 -> "aq1", ...
			self._qubit_index_to_name = {
				q: f"aq{q}" for q in sorted(set(qubits))
			}
		
		# 初始化 SISQ 环境
		self._initialize_sisq_environment(with_reset)
		
		# 如果有传入的 gates（SISQ Gate），直接添加到函数中
		if gates:
			for gate in gates:
				self.add_gate(gate)
	
	def _initialize_sisq_environment(self, with_reset: bool):
		"""初始化 SISQ 程序的基本结构"""
		# 1. 加载 gm 模块
		self.load_module_set(Module.gm)
		
		# 2. 生成 layout 段（声明物理量子比特）
		phy_qubits = [
			PhyQubit(self._qubit_index_to_name[q]) 
			for q in sorted(self._qubit_index_to_name.keys())
		]
		if phy_qubits:
			qubit_decl = QubitDeclaration(phy_qubits)
			self.add_layout_qubit_decl(qubit_decl)
		
		# 3. 创建 quantum_circuit 函数
		func = Function()
		func.init_name(self.QUANTUM_CIRCUIT_FUNC_NAME)
		func.init_input_args([])
		func.init_output_args([])
		
		# 4. 如果需要，添加 reset 操作
		if with_reset and phy_qubits:
			reset_call = FuncCall("reset", phy_qubits, [])
			func.add_instruction(reset_call)
		
		# 5. 将函数添加到 code 段
		self.add_define_function(func)
		
		# 6. 生成 entry 段
		entry_call = FuncCall(self.QUANTUM_CIRCUIT_FUNC_NAME, [], [])
		self.add_entry_instruction(entry_call)
	
	@property
	def qubits(self) -> List[int]:
		"""
		返回 EGM 风格的 qubit index 列表（向后兼容）。
		注意：为了兼容现有代码，返回 int 类型列表。
		"""
		return sorted(self._qubit_index_to_name.keys())
	
	@property
	def phy_qubits(self) -> List[PhyQubit]:
		"""
		返回 SISQ 风格的 PhyQubit 对象列表。
		这是新增属性，用于直接访问 SISQ 原生的 qubit 表示。
		"""
		return [
			PhyQubit(self._qubit_index_to_name[q]) 
			for q in sorted(self._qubit_index_to_name.keys())
		]
	
	@property
	def gates(self) -> List:
		"""
		返回 SISQ Gate 对象列表。
		从 SISQ 的 quantum_circuit 函数中提取所有门操作（跳过 reset 和 measure）。
		"""
		# 获取 quantum_circuit 函数
		try:
			func = self.code_section.get_func(self.QUANTUM_CIRCUIT_FUNC_NAME)
		except ValueError:
			return []
		
		# 提取所有门操作（跳过 reset 和 measure 调用）
		gates = []
		for insn in func.body:
			# 跳过 reset 和 measure 调用
			if isinstance(insn, FuncCall):
				if insn.opname in ["reset", "measure"]:
					continue
			
			# 其他指令（SISQ Gate）直接添加
			# 注意：这里假设所有非 reset/measure 的指令都是 Gate
			gates.append(insn)
		
		return gates
	
	@property
	def num_qubits(self) -> int:
		"""返回量子比特数量"""
		return len(self._qubit_index_to_name)
```

#### 7.2 重写核心方法
直接操作 SISQ Gate 对象，不再进行转换。

```python
# 旧实现（EGM Gate）
def add_gate(self, g: Gate): 
	self.gates.append(g)  # EGM Gate

def add_gates(self, gs: List[Gate]): 
	self.gates.extend(gs)  # EGM Gate 列表

# 新实现（SISQ Gate）
def add_gate(self, g):
	"""
	将 SISQ Gate 对象添加到 quantum_circuit 函数中。
	
	Args:
		g: SISQ Gate 对象（如 H, CNOT, Rx 等，来自 sisq.ast.modules.gate）
	"""
	# 获取 quantum_circuit 函数
	func = self.code_section.get_func(self.QUANTUM_CIRCUIT_FUNC_NAME)
	
	# 直接添加 SISQ Gate 指令
	func.add_instruction(g)

def add_gates(self, gs: List):
	"""批量添加 SISQ Gate 对象"""
	func = self.code_section.get_func(self.QUANTUM_CIRCUIT_FUNC_NAME)
	for g in gs:
		func.add_instruction(g)

def measure_all(self, is_multi_readout: bool = True):
	"""
	添加测量操作。
	
	Args:
		is_multi_readout: 如果为 True，使用单个 measure 调用测量所有 qubit；
		                 如果为 False，为每个 qubit 单独调用 measure
	"""
	func = self.code_section.get_func(self.QUANTUM_CIRCUIT_FUNC_NAME)
	phy_qubits = self.phy_qubits
	
	if is_multi_readout and phy_qubits:
		# 多路测量：measure($aq0, $aq1, ...)
		measure_call = FuncCall("measure", phy_qubits, [])
		func.add_instruction(measure_call)
	else:
		# 单独测量：为每个 qubit 调用 measure
		for q in phy_qubits:
			measure_call = FuncCall("measure", [q], [])
			func.add_instruction(measure_call)
```

#### 7.3 重写其他核心方法
保持接口兼容，但内部完全基于 SISQ。

```python
def copy(self) -> "QuantumCircuit":
	"""创建当前电路的深拷贝"""
	# 创建新的 QuantumCircuit
	new_circuit = QuantumCircuit(
		qubits=self.qubits[:],
		qubit_name_map=self._qubit_index_to_name.copy(),
		with_reset=False  # 避免重复添加 reset
	)
	
	# 复制元数据
	new_circuit.metadata = self.metadata.copy()
	
	# 复制所有指令（包括门操作）
	func = self.code_section.get_func(self.QUANTUM_CIRCUIT_FUNC_NAME)
	new_func = new_circuit.code_section.get_func(self.QUANTUM_CIRCUIT_FUNC_NAME)
	
	# 跳过 reset 调用（已经在初始化时添加）
	for insn in func.body:
		if isinstance(insn, FuncCall) and insn.opname == "reset":
			continue
		# 深拷贝指令
		new_func.add_instruction(insn)
	
	return new_circuit

def __add__(self, other: "QuantumCircuit") -> "QuantumCircuit":
	"""合并两个电路"""
	if not isinstance(other, QuantumCircuit):
		return NotImplemented
	
	# 合并 qubit 列表
	all_qubits = sorted(set(self.qubits) | set(other.qubits))
	
	# 合并 qubit 名称映射
	merged_map = self._qubit_index_to_name.copy()
	merged_map.update(other._qubit_index_to_name)
	
	# 创建新电路
	result = QuantumCircuit(
		qubits=all_qubits,
		qubit_name_map=merged_map,
		with_reset=False
	)
	result.metadata = {**other.metadata, **self.metadata}
	
	# 添加第一个电路的门（跳过 reset）
	func1 = self.code_section.get_func(self.QUANTUM_CIRCUIT_FUNC_NAME)
	result_func = result.code_section.get_func(self.QUANTUM_CIRCUIT_FUNC_NAME)
	
	for insn in func1.body:
		if isinstance(insn, FuncCall) and insn.opname == "reset":
			continue
		result_func.add_instruction(insn)
	
	# 添加第二个电路的门（跳过 reset）
	func2 = other.code_section.get_func(self.QUANTUM_CIRCUIT_FUNC_NAME)
	for insn in func2.body:
		if isinstance(insn, FuncCall) and insn.opname == "reset":
			continue
		result_func.add_instruction(insn)
	
	return result

def inverse(self) -> "QuantumCircuit":
	"""返回电路的逆电路"""
	# 获取当前函数
	func = self.code_section.get_func(self.QUANTUM_CIRCUIT_FUNC_NAME)
	
	# 创建逆电路
	inv_circuit = QuantumCircuit(
		qubits=self.qubits[:],
		qubit_name_map=self._qubit_index_to_name.copy(),
		with_reset=False
	)
	inv_circuit.metadata = self.metadata.copy()
	inv_circuit.metadata["name"] = self.metadata.get("name", "circuit") + "_dg"
	
	inv_func = inv_circuit.code_section.get_func(self.QUANTUM_CIRCUIT_FUNC_NAME)
	
	# 反转指令顺序并取逆
	reversed_insns = []
	for insn in reversed(func.body):
		if isinstance(insn, FuncCall) and insn.opname in ["reset", "measure"]:
			continue
		
		# SISQ Gate 对象有 inverse 方法
		if hasattr(insn, 'inverse'):
			inv_insn = insn.inverse()
			if inv_insn is not None:
				reversed_insns.append(inv_insn)
	
	# 添加逆指令
	for insn in reversed_insns:
		inv_func.add_instruction(insn)
	
	return inv_circuit

def decompose(
	self,
	basis_gates: List[str],
	custom_rules: Optional[Dict[str, "DecompositionRule"]] = None
) -> "QuantumCircuit":

	# TODO: 
  # 在实现该方法前：
  # 需要将如下目前各门的分解形式使用SISQ重写
  # CNOT_BASED_DECOMPOSITIONS = {
  #  "cz": lambda c, t: [Gate("h", (t,)), Gate("cnot", (c, t)), Gate("h", (t,))],
  #}
  
