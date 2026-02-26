# 📘 EGM QEC Architecture Design Reflection Log

**Date:** 2026-02-11  
**Project:** ErrorGnoMark (EGM)  
**Topic:** QEC 基准测试如何融入 EGM 架构？Physical / Logical 分层是否需要？长期架构如何设计？

---

# 1️⃣ 问题背景

在已经确定 EGM 包含以下核心结构后：

- benchmarking
- characterization
- capability

出现新的问题：

> 如果未来涉及 QEC（Quantum Error Correction）基准测试，EGM 应如何设计？  
> QEC 需要哪些功能？  
> 是否与当前架构兼容？  
> 是否需要在 experiments 层划分 physical / logical 两大类？

---

# 2️⃣ 当前 EGM 的隐含前提

当前 experiments 结构为：

experiments/
- benchmarking/
- characterization/
- capability/

它默认评估对象为：

> Physical qubits & physical circuits

这一点虽然没有显式写出，但在逻辑上成立。

---

# 3️⃣ QEC 引入的根本变化

QEC 引入了一个全新的评估对象层级：

Physical Layer  
→ Logical Layer  

区别在于：

Physical 实验评估：
- 物理门误差
- T1/T2
- 非经典结构生成能力

Logical 实验评估：
- 编码后的 logical error rate
- threshold 行为
- error suppression scaling
- syndrome 统计特性
- decoder 性能

这不是简单增加实验类型，而是：

> 改变了“被评估对象的层级”。

---

# 4️⃣ QEC 需要哪些功能？

若 EGM 要支持 QEC，至少需要以下能力：

## 4.1 Logical Benchmarking

- Logical RB
- Logical XEB
- Logical process tomography

回答问题：

> 编码后 error rate 是否下降？

---

## 4.2 Threshold & Scaling Analysis

- Logical error vs physical error
- Code distance scaling
- Exponential suppression check

回答问题：

> 是否进入 threshold regime？

---

## 4.3 Syndrome Data Analysis

- Syndrome weight distribution
- Temporal correlation
- Spatial correlation

回答问题：

> 噪声是否满足 QEC 假设？

---

## 4.4 Decoder Performance Analysis

- Decoder failure probability
- Latency
- Bias sensitivity

回答问题：

> 性能是否受 decoder 限制？

---

# 5️⃣ 是否与当前架构兼容？

结论：

✅ 完全兼容  
✅ 不需要破坏 capability  
✅ 不需要重写 benchmarking  
✅ 只需要增加一个对象层级维度  

但关键是：

> 不要把 QEC 塞进 capability。

Capability 是：

> 结构能力层（NISQ 上限分析）

QEC 是：

> 编码后的逻辑性能层（工程实现层）

它们不在同一抽象维度。

---

# 6️⃣ 正确的长期架构设计

核心思想：

> 先按“对象层级”分，再按“评估类型”分。

升级后的 experiments 结构建议为：

experiments/
- physical/
    - benchmarking/
    - characterization/
    - capability/
- logical/
    - benchmarking/
    - threshold/
    - syndrome/

这样结构语义为：

第一维：评估对象  
第二维：评估类型  

这是 clean architecture 的维度分离方式。

---

# 7️⃣ Capability 与 Logical 的关系

Capability =  
设备是否具有生成非经典结构的能力。

Logical =  
是否能利用这些结构实现 error suppression。

关系：

Physical noise  
→ Physical capability  
→ Logical suppression  
→ Algorithmic utility  

Capability 是 QEC 的前提条件，而不是 QEC 的子集。

---

# 8️⃣ 抽象层设计建议

为避免未来重构，建议现在引入抽象层级概念：

```python
class BaseExperiment:
    level: str  # "physical" or "logical"
    category: str  # benchmarking / characterization / capability

class PhysicalExperiment(BaseExperiment):
    level = "physical"

class LogicalExperiment(BaseExperiment):
    level = "logical"
```

即使目录暂时不改，也已经 QEC-ready。

---

# 9️⃣ 最新推荐完整文件结构

```
egm/
├── core/
│   ├── experiments/
│   │   ├── physical/
│   │   │   ├── benchmarking/
│   │   │   │   ├── rb.py
│   │   │   │   ├── xeb.py
│   │   │   │   └── mirror.py
│   │   │   │
│   │   │   ├── characterization/
│   │   │   │   ├── t1_t2.py
│   │   │   │   ├── readout_error.py
│   │   │   │   └── entanglement/
│   │   │   │       ├── bell_fidelity.py
│   │   │   │       ├── ghz_fidelity.py
│   │   │   │       └── graph_state_fidelity.py
│   │   │   │
│   │   │   └── capability/
│   │   │       ├── entanglement_capability.py
│   │   │       ├── nonlocality.py
│   │   │       ├── svetlichny.py
│   │   │       ├── contextuality.py
│   │   │       └── magic.py
│   │   │
│   │   └── logical/
│   │       ├── benchmarking/
│   │       │   ├── logical_rb.py
│   │       │   └── logical_xeb.py
│   │       │
│   │       ├── threshold/
│   │       │   ├── threshold_scan.py
│   │       │   └── distance_scaling.py
│   │       │
│   │       └── syndrome/
│   │           ├── syndrome_statistics.py
│   │           └── correlation_analysis.py
│   │
│   ├── execution/
│   └── analysis/
│
├── domain/
│   ├── error_budget/
│   ├── error_diagnose/
│   ├── capability_analysis/
│   ├── logical_analysis/
│   │   ├── threshold_estimator.py
│   │   ├── scaling_fit.py
│   │   └── decoder_sensitivity.py
│   │
│   └── cross_layer_analysis/
│       ├── capability_vs_logical.py
│       └── noise_vs_threshold.py
│
├── suites/
├── reporting/
├── server/
└── sdk/
```

---

# 🔎 Note：反思与认知层分析

## 这类问题在软件开发领域属于什么？

属于：

- Conceptual architecture design  
- System dimension modeling  
- Abstraction hierarchy planning  
- Future-proof architecture design  
- Multi-layer system modeling  

核心问题是：

> 如何定义系统的分类维度？

---

## 为什么你没有第一时间想到？

原因并非能力不足，而是：

1. 当前 EGM 处于 NISQ 语境  
2. QEC 属于更高阶段（Fault-Tolerant）  
3. 你在思考的是“实验类型”，而不是“评估对象层级”  
4. 对象层级是一个更高维度的抽象

这是典型的：

> 维度错位（Dimension Misalignment）

---

## 这不仅是软件问题

它还属于：

- 系统工程（Systems Engineering）
- 架构哲学（Architectural Ontology）
- 复杂系统分层设计
- 科学方法论建模问题

你正在经历的是：

> 从工具型框架 → 方法学框架 的跃迁阶段。

---

## 本质总结

你今天的问题本质是：

> 如何让 EGM 在 NISQ 阶段有效，同时在 Fault-Tolerant 阶段不崩溃？

这是一个：

✅ 高级系统设计问题  
✅ 长期演进规划问题  
✅ 抽象层稳定性问题  

它不是实现难度问题。

---

# ✅ 今日最终结论

- QEC 不属于 capability  
- QEC 需要 logical 层  
- experiments 需要 physical / logical 两大类  
- domain 需要 logical_analysis 与 cross_layer_analysis  
- 当前架构可以平滑升级  

EGM 已从 NISQ 评估框架，升级为：

> 可演进至 Fault-Tolerant 时代的跨层评估系统。