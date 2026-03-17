# 📘 EGM 架构共识文档  
**版本：v1.0**  
**作者角色：项目负责人 / 架构审核人**  
**目标读者：两位实习生（协作开发）**  
**目的：建立统一架构认知，避免跨层耦合，保证系统可持续演化**

---

# 一、为什么必须读这份文档？

EGM 不是一个“实验脚本集合”。

EGM 是一个：

> ✅ 带时间结构的硬件语义演化系统  
> ✅ 事件驱动的版本化世界模型  
> ✅ 可追溯、可解释的硬件认知引擎  

如果架构理解不统一，后果会是：

- 层级混乱
- 模块互相调用
- Version 逻辑被绕过
- 无法审计
- 无法长期维护

我最终扮演 **审核者角色**。  
你们的设计必须符合下面的结构约束。

---

# 二、EGM 的五层模型（必须记住）

```
┌──────────────────────────┐
│      Execution Layer      │  ← Suite / Plan
└─────────────┬────────────┘
              ↓
┌──────────────────────────┐
│      Experiment Layer     │  ← 定义实验
└─────────────┬────────────┘
              ↓
┌──────────────────────────┐
│       Analysis Layer      │  ← 数值处理
└─────────────┬────────────┘
              ↓
┌──────────────────────────┐
│        Domain Layer       │  ← 语义判断
└─────────────┬────────────┘
              ↓
┌──────────────────────────┐
│         System Core       │  ← Version / State
└──────────────────────────┘
```

---

# 三、每一层的职责边界（不可越界）

---

## 1️⃣ Execution Layer（Suite / Plan）

📂 对应模块：

```
egm/execution/
```

### 职责：

- 编排实验组合（例如 RB + XEB）
- 控制执行顺序
- 调度运行
- 组织批量流程

### 解决问题：

> HOW to measure?

### 严禁：

- ❌ 修改 HardwareState
- ❌ 创建 Version
- ❌ 调用 version.apply
- ❌ 生成 Event

---

## 2️⃣ Experiment Layer

📂 对应模块：

```
egm/experiments/
```

### 职责：

- 定义实验类型（RB、XEB、Tomography 等）
- 执行实验
- 产生 Raw Data

输出：

```
raw_data
```

### 严禁：

- ❌ 生成 Version
- ❌ 修改系统状态
- ❌ 做语义判断

---

## 3️⃣ Analysis Layer（数值层）

📂 对应模块：

```
egm/analysis/
```

### 职责：

- 拟合
- 统计
- 误差计算
- 指标生成

输入：

```
raw_data
```

输出：

```
metrics = { ... }
```

### 解决问题：

> 数值是多少？

### 严禁：

- ❌ 生成 Event
- ❌ 调用 Version
- ❌ 触碰 System

---

## 4️⃣ Domain Layer（语义层）

📂 对应模块：

```
egm/domain/
    error_analysis/
    error_inference/
    error_modeling/
```

### 职责：

- 判断 metrics 是否构成“语义变化”
- 生成强类型 Event
- 决定是否需要创建新 Version

输入：

```
metrics
```

输出：

```
Event | None
```

### 解决问题：

> 这意味着什么？

---

## 5️⃣ System Core（时间内核）

📂 对应模块：

```
egm/domain/system/
```

包含：

- HardwareState（不可变）
- Event（变化声明）
- Version（时间节点）
- Snapshot（只读视图）

### 唯一入口：

```
Version.apply(event)
```

### 解决问题：

> 世界如何随时间演化？

---

# 四、核心原则（必须达成共识）

---

## ✅ 原则 1：只有 Event 可以改变世界

```
Experiment 不能改世界
Analysis 不能改世界
Suite 不能改世界
只有 Event 能
```

---

## ✅ 原则 2：State 是不可变的

```
State_{n+1} = f(State_n, Event)
```

- State 不知道时间
- Version 管理时间
- Event 描述变化

---

## ✅ 原则 3：严格单向数据流

```
Suite
  ↓
Experiment
  ↓
Analysis
  ↓
Domain
  ↓
Event
  ↓
Version.apply
```

绝不允许反向依赖。

---

# 五、RB + XEB 示例流程（具体可视化）

假设 Suite 执行 RB + XEB。

---

## Step 1：Suite 编排

```
CalibrationSuite:
    - RBExperiment
    - XEBExperiment
```

---

## Step 2：Experiment 执行

```
rb_raw_data
xeb_raw_data
```

---

## Step 3：Analysis

```
rb_metrics
xeb_metrics
```

---

## Step 4：Domain 生成 Event

可能产生：

```
PerformanceDegradationEvent
```

或者：

```
None
```

---

## Step 5：System 更新

```
new_version = current_version.apply(event)
```

Version DAG：

```
V0 → V1 → V2
```

---

# 六、两位实习生的协作分工建议

为了避免交叉耦合：

---

## 👨‍🔬 实习生 A（执行与分析方向）

负责：

- Suite 设计
- Experiment 实现
- Analysis 模块

不得触碰：

- Version
- Event 定义
- HardwareState

---

## 👨‍🔬 实习生 B（语义与系统方向）

负责：

- Event 定义
- Domain 语义判断
- Version.apply 逻辑
- HardwareState 建模

不得触碰：

- Experiment 内部实现
- Suite 调度逻辑

---

## ✅ 协作接口

两人通过一个清晰接口对接：

```
metrics → domain.generate_event(metrics)
```

这是唯一桥梁。

---

# 七、审核标准（我将使用）

我会检查：

1. 是否有跨层调用？
2. 是否有 Experiment 直接改 State？
3. 是否有 Analysis 直接生成 Event？
4. 是否有 Suite 调用 Version？
5. 是否保证 Version 是唯一时间入口？
6. 是否保持 State 不可变？

任何违反都会被要求重构。

---

# 八、常见错误（提前避免）

❌ 在 analysis 中写：

```python
if error > threshold:
    version.apply(...)
```

❌ 在 Suite 中写：

```python
event = PerformanceEvent(...)
```

❌ 在 Experiment 中 import system

---

# 九、这套架构的长期价值

如果严格遵守：

- ✅ 可追溯历史
- ✅ 可回滚
- ✅ 可审计
- ✅ 可解释
- ✅ 可演化
- ✅ 可扩展到自动决策系统

如果不遵守：

- ❌ 状态污染
- ❌ 无法审计
- ❌ 时间结构崩溃
- ❌ 技术债快速积累

---

# 十、最终共识

EGM 不是一个“实验执行框架”。

EGM 是一个：

> 事件驱动的版本化硬件世界模型。

请在写任何代码前，先问自己：

> 我现在写的逻辑属于哪一层？

如果不确定，必须先讨论。

---

# 结语

这份架构不是形式主义。  
这是为了保证系统三年后仍然清晰可控。

你们负责实现。  
我负责守住结构边界。

我们目标不是“跑通代码”。

我们目标是：

> 建立一个可持续演化的硬件认知引擎。