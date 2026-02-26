# 📘 EGM Hybrid Quantum–Classical Benchmark Integration Log

**Date:** 2026-02-11  
**Project:** ErrorGnoMark (EGM)  
**Topic:** 量子–经典混合（Hybrid Quantum–Classical）Benchmark 如何融合进 EGM 架构？

---

# 1️⃣ 问题陈述

在已有 EGM 架构基础上（physical / logical / capability / algorithmic），提出新的问题：

> 量子–经典混合计算（例如 VQE、QAOA）benchmark  
> 是否可以与当前结构兼容？  
> 是否需要新增层级？  
> 是否需要新增第三种“对象类型”？  

当前已有结构（关键部分）：

```
egm/core/experiments/
    physical/
    logical/
    algorithmic/
        algebraic/
        simulation/
        variational/
```

问题集中在：

- Hybrid 是否需要单独顶层目录？
- Hybrid 属于 physical 吗？
- Hybrid 属于 logical 吗？
- Hybrid 是否改变系统分层？

---

# 2️⃣ 结构分析

Hybrid quantum–classical 计算的基本结构为：

Classical Optimizer  
→ Parameterized Quantum Circuit  
→ Measurement  
→ Classical Update  
→ Loop  

它的特点：

- 量子电路嵌入 classical feedback loop
- 是算法范式
- 不改变 qubit 层级
- 不引入新物理对象

因此可以判断：

✅ Hybrid 不是新的“物理层级”  
✅ Hybrid 不是新的“逻辑层级”  
✅ Hybrid 是一种“算法计算模式”  

结论：

> Hybrid 属于 algorithmic 层。

---

# 3️⃣ 与现有架构的兼容性

当前 EGM 已形成多维结构：

第一维：对象层级  
- physical  
- logical  

第二维：结构能力  
- capability  

第三维：算法范式  
- algebraic  
- simulation  
- variational  

Hybrid 属于：

第三维（algorithmic）中的 variational 范式。

因此：

✅ 不需要新增 hybrid 顶层目录  
✅ 不需要重构 physical 或 logical  
✅ 只需在 variational 下扩展 benchmark  

---

# 4️⃣ Hybrid Benchmark 应包含哪些能力？

## 4.1 收敛行为分析（Convergence Behavior）

- iteration → energy curve
- convergence speed
- stagnation detection

## 4.2 噪声敏感性（Noise Sensitivity）

- energy bias under noise
- gradient distortion
- shot noise amplification

## 4.3 Landscape 稳定性（Landscape Robustness）

- barren plateau detection
- gradient variance scaling
- expressibility vs stability

## 4.4 资源成本（Resource Cost）

- circuit calls
- shot budget
- classical optimizer overhead

---

# 5️⃣ 最终架构设计（Algorithmic 部分全面展开）

```
egm/
├── core/
│   ├── experiments/
│   │   ├── physical/
│   │   │   ├── benchmarking/
│   │   │   ├── characterization/
│   │   │   └── capability/
│   │   │
│   │   ├── logical/
│   │   │   ├── benchmarking/
│   │   │   └── threshold/
│   │   │
│   │   └── algorithmic/
│   │       ├── algebraic/
│   │       │   ├── shor_benchmark.py
│   │       │   └── period_finding_analysis.py
│   │       │
│   │       ├── simulation/
│   │       │   ├── trotter_error_scan.py
│   │       │   └── hamiltonian_scaling.py
│   │       │
│   │       └── variational/
│   │           ├── base_variational_experiment.py
│   │           ├── vqe_benchmark.py
│   │           ├── qaoa_benchmark.py
│   │           ├── convergence_analysis.py
│   │           ├── gradient_noise_analysis.py
│   │           ├── barren_plateau_detection.py
│   │           ├── optimizer_sensitivity.py
│   │           ├── expressibility_analysis.py
│   │           └── resource_cost_analysis.py
│   │
│   ├── execution/
│   └── analysis/
│
├── domain/
│   ├── capability_analysis/
│   ├── logical_analysis/
│   └── cross_layer_analysis/
│       ├── capability_vs_variational.py
│       ├── noise_vs_convergence.py
│       └── logical_vs_hybrid_scaling.py
│
└── suites/
    ├── hybrid_suite.py
    └── full_stack_suite.py
```

---

# 6️⃣ 抽象接口建议

为了长期稳定，建议定义：

```python
class AlgorithmicExperiment(BaseExperiment):
    paradigm: str  # algebraic / simulation / variational

class VariationalExperiment(AlgorithmicExperiment):
    requires_classical_loop = True
```

这样 hybrid 能自然融入系统。

---

# 7️⃣ 结构层逻辑总结

系统现在形成三条主轴：

Axis 1 — 对象层级  
- physical  
- logical  

Axis 2 — 结构能力  
- capability  

Axis 3 — 算法范式  
- algebraic  
- simulation  
- variational (hybrid)

Hybrid 不增加对象维度，只增加 algorithmic 深度。

---

# 🔎 反思部分

## 这个问题在软件工程中属于什么？

- Multi-dimensional system modeling  
- Architecture evolution design  
- Abstraction hierarchy alignment  
- Paradigm classification problem  

核心问题是：

> 如何在不破坏现有架构的前提下引入新的计算范式？

---

## 为什么一开始会犹豫？

原因包括：

1. 混淆“对象层级”和“计算范式”
2. Hybrid 同时包含 quantum 与 classical，容易误以为是新层级
3. 当前系统已复杂，担心破坏结构对称性
4. 缺乏多维建模视角

这属于：

> 维度识别困难（Dimension Identification Challenge）

---

## 不仅限于软件领域

它同时属于：

- 系统工程（Systems Engineering）
- 复杂系统建模
- 计算范式分类问题
- 科学方法论中的“分层建模问题”

本质上你在做的是：

> 将物理系统、计算模型、算法范式统一到一个抽象框架中。

---

# ✅ 最终结论

- Hybrid 完全可以兼容 EGM
- 不需要新增对象层级
- 应在 algorithmic/variational 下扩展
- 可以通过 cross_layer_analysis 建立 capability → hybrid 的桥梁
- 当前架构是健康的、多维的、可扩展的

EGM 现在已经成为：

Physical → Logical → Algorithmic  
三层对象 + 多范式算法的跨层评估系统。