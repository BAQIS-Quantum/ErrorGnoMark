# EGM 核心设计原则（Core Design Principles）

作者：项目负责人  
状态：核心架构约束文件  
适用范围：EGM system/core 层的所有修改与扩展  

---

## 一、本文档目的

本文档用于明确 EGM 核心语义层的技术不变量（Architectural Invariants）。

这些原则具有约束性意义：

- 不因短期功能需求而修改；
- 不因单一应用场景而破坏；
- 不因实现便利性而妥协。

任何对 core 层（system/ 或等价目录）的结构修改，必须满足本文档定义的原则。

---

## 二、核心设计不变量总览

EGM 的核心技术不变量包括：

1. 状态不可变原则（State Immutability）
2. 事件唯一演化原则（Event-Driven Evolution）
3. 显式时间结构原则（Explicit Temporal Modeling）
4. 读写路径分离原则（Read/Write Separation）
5. 版本绑定访问原则（Version-Bound Access）
6. 语义优先于数值原则（Semantic Over Numeric Representation）
7. 核心层确定性原则（Deterministic Core Principle）

以下分别说明。

---

## 三、状态不可变原则（State Immutability）

### 3.1 原则定义

一旦生成某个 Version 对应的 HardwareState，该状态对象不得被修改。

状态演化只能通过生成新的 Version 实现。

### 3.2 技术意义

- 防止隐式状态污染；
- 保证历史一致性；
- 支持回溯与解释；
- 使系统具备引用透明性。

### 3.3 禁止行为

- 直接修改 HardwareState 内部字段；
- 在 Snapshot 中暴露可写接口；
- 在应用层缓存并修改状态对象。

---

## 四、事件唯一演化原则（Event-Driven Evolution）

### 4.1 原则定义

所有状态变化必须通过 Event 触发。

不得存在“隐式状态更新路径”。

### 4.2 演化路径约束

合法路径：

Event → apply() → new HardwareState → new Version → Snapshot

非法路径包括：

- 直接构造新状态绕过 Event；
- 修改已有 Version；
- 从外部模块直接注入状态。

### 4.3 原则意义

- 保证状态变化具有可解释来源；
- 保证时间结构完整；
- 支持历史因果追溯。

---

## 五、显式时间结构原则（Explicit Temporal Modeling）

### 5.1 原则定义

时间必须通过 Version Graph 显式表达。

禁止使用覆盖式更新表示时间演化。

### 5.2 Version Graph 要求

- Version 形成有向无环图（DAG）；
- 每个 Version 必须绑定唯一父节点或父集合；
- 不得修改历史节点。

### 5.3 原则意义

- 支持分支分析；
- 支持历史回溯；
- 支持实验条件比较。

---

## 六、读写路径分离原则（Read/Write Separation）

### 6.1 原则定义

系统必须严格区分：

- 写路径：Execution → Analysis → Event → Version
- 读路径：Version → Snapshot → Application

### 6.2 约束

- 应用层只允许通过 Snapshot 读取；
- 应用层不得参与 Version 构造；
- Snapshot 不提供写接口。

### 6.3 原则意义

- 防止跨层耦合；
- 保证状态演化可控；
- 降低副作用风险。

---

## 七、版本绑定访问原则（Version-Bound Access）

### 7.1 原则定义

所有外部决策行为必须绑定具体 Version。

禁止存在“无版本上下文”的状态访问。

### 7.2 技术含义

- 编译决策必须绑定 Version ID；
- 校准分析必须明确引用 Version；
- 历史分析必须显式选择时间点。

### 7.3 原则意义

- 支持决策可解释性；
- 保证时间一致性；
- 避免状态漂移问题。

---

## 八、语义优先于数值原则（Semantic Over Numeric Representation）

### 8.1 原则定义

EGM 表达的是“语义状态变化”，而不仅是数值参数变化。

Event 表示的是“世界认知变化”，而不是简单的数值更新。

### 8.2 实现约束

- 不将原始数值直接等同为语义状态；
- 必须通过语义判断生成 Event；
- Domain 层可分析数据，但 core 只接收语义声明。

### 8.3 原则意义

- 提升抽象层次；
- 避免系统退化为参数数据库；
- 保持世界模型定位。

---

## 九、核心层确定性原则（Deterministic Core Principle）

### 9.1 原则定义

Core 层仅表达已发生事实。

概率预测、风险估计等应作为扩展层存在。

### 9.2 禁止行为

- 在 HardwareState 中引入概率字段；
- 在 Version 中引入预测结果；
- 在 Snapshot 中混入未来推断。

### 9.3 原则意义

- 保持核心语义纯净；
- 防止历史事实与未来推断混淆；
- 支持可验证性与可复现实验。

---

## 十、修改与评审规则

任何对 core 层的修改必须满足：

1. 不破坏上述不变量；
2. 不引入隐式写路径；
3. 不降低时间结构清晰度；
4. 不为单一应用定制抽象。

如需例外情况，必须经过架构评审讨论并形成书面记录。

---

## 十一、总结

EGM 的长期稳定性取决于：

- 抽象边界的清晰性；
- 状态演化路径的唯一性；
- 时间结构的显式表达；
- 核心层的语义纯净性。

本文件定义的技术不变量具有长期约束意义。
任何核心设计决策，必须以本文件为判断依据。