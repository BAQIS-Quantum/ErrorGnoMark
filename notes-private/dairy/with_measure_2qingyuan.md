# Benchmark 电路中测量策略的组件化调整说明

## 问题

目前在 egm 的 benchmark 实现中（如 CSB），电路在生成阶段直接调用了 `measure_all()`，将“是否进行测量”这一**实验执行策略**写死进了电路结构本身。这种做法在功能上是可行的，但在工程上存在明显限制：

- 电路难以复用（例如用于理想仿真、无测量分析或不同 backend）
- 无法支持非全测量或由执行层决定测量方式
- 将实验协议层的决策耦合进了电路（IR）层

从架构角度看，这属于职责边界不清的问题。

---

## 解决方案

将“是否插入测量”作为 **benchmark / experiment 层** 的显式参数（例如 `with_measurement`），而不是放在 `QuantumCircuit` 层。

设计原则如下：

- `QuantumCircuit` 只负责表达量子演化本身（gate、顺序、结构）
- 是否插入测量属于实验协议的一部分，应由 benchmark / experiment 层控制
- 默认行为保持与当前实现一致（`with_measurement=True`）
- 未来更复杂的能力（如 mid-circuit measurement、量子–经典反馈）由 backend / executor 层负责演化，而不是提前在 circuit 或 benchmark 层预留接口

---

## 代码示意

```python
# benchmark 层：电路生成函数
def generate_*_circuits(..., with_measurement: bool = True):
    circ = QuantumCircuit(...)
    ...
    if with_measurement:
        circ.measure_all()
    return circ


# benchmark / experiment 层：实验对象
class SomeBenchmarkExperiment:
    def __init__(..., with_measurement: bool = True):
        self.with_measurement = with_measurement

    def run(...):
        generate_*_circuits(
            ...,
            with_measurement=self.with_measurement,
        )