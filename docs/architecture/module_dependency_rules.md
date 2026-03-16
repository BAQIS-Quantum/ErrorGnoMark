# EGM 模块依赖与调用约束（Module Dependency Rules）

作者：项目负责人  
状态：架构依赖约束文件  
适用范围：EGM 全部模块  

---

## 一、本文档目的

本文档用于明确 EGM 各模块之间的依赖方向与调用边界。

目标包括：

- 防止层级反转；
- 防止跨层耦合；
- 保证核心语义层稳定；
- 支持系统长期演化。

本文件为结构性约束文件，具有工程执行意义。

---

## 二、总体层级划分

当前 EGM 结构可抽象为如下层级：

Level 0：Core 语义层（system / core）  
Level 1：Domain 语义扩展层（domain）  
Level 2：Intelligence 扩展层（intelligence）  
Level 3：Application 层（suites / compiler / calibration 等）  
Level 4：Execution 输入层（execution / experiments）  

---

## 三、依赖方向总原则

依赖方向必须单向流动：

Execution → Domain → Core  
Core → Snapshot → Intelligence → Application  

更严格表达为：

- 下层不得依赖上层；
- 扩展层不得修改核心层；
- 应用层不得绕过 Snapshot。

禁止出现循环依赖。

---

## 四、Core 层（Level 0）

### 4.1 允许依赖

Core 层仅可依赖：

- 标准库；
- 基础数据结构；
- 不包含上层语义的基础模块（如 types）。

Core 不得依赖：

- domain；
- intelligence；
- suites；
- execution；
- experiments。

### 4.2 调用约束

Core 提供：

- HardwareState
- Event
- Version
- Snapshot

其他层只能通过公开接口调用。

Core 不应感知：

- 编译逻辑；
- 校准策略；
- AI 模型；
- 实验调度。

---

## 五、Domain 层（Level 1）

### 5.1 职责

Domain 负责：

- 对实验数据进行语义判断；
- 构造合法 Event；
- 执行误差分析与建模。

### 5.2 允许依赖

Domain 可以依赖：

- Core；
- datastore；
- analysis 工具。

### 5.3 禁止行为

Domain 不得：

- 修改 HardwareState 内部结构；
- 创建绕过 Event 的状态更新；
- 修改 Version 生成逻辑；
- 在 Core 中新增字段以适配单一分析需求。

Domain 只能通过：

Event → Core.apply()

进行状态更新。

---

## 六、Intelligence 层（Level 2）

### 6.1 职责

Intelligence 层负责：

- 时间序列分析；
- 预测模型；
- 风险估计；
- 研究性算法。

### 6.2 允许依赖

Intelligence 可以依赖：

- Core（只读 Snapshot）；
- Domain 输出；
- 数据查询接口。

### 6.3 禁止行为

Intelligence 不得：

- 修改 Version；
- 修改 HardwareState；
- 在 Snapshot 中添加可写接口；
- 将预测结果写入 Core。

预测结果必须作为独立结构存在。

---

## 七、Application 层（Level 3）

### 7.1 职责

Application 层包括：

- Compiler；
- Calibration 策略；
- Scheduling；
- Benchmark。

### 7.2 访问方式

Application 只能：

- 读取 Snapshot；
- 读取 PredictiveContext（若存在）。

Application 不得：

- 构造 Version；
- 修改 HardwareState；
- 绕过 Event 机制。

---

## 八、Execution 层（Level 4）

### 8.1 职责

Execution 层负责：

- 实验执行；
- 原始数据生成；
- 参数拟合。

Execution 输出“事实数据”。

### 8.2 与 Core 的关系

Execution 不直接修改 Core。

合法路径为：

Execution → Domain Analysis → Event → Core

---

## 九、跨层调用规则总结

| 层级 | 可读取 | 可调用 | 不可操作 |
|------|--------|--------|----------|
| Core | 无 | 内部 | 不依赖上层 |
| Domain | Core | Event.apply | 不修改结构 |
| Intelligence | Snapshot | 只读接口 | 不写入 Core |
| Application | Snapshot | 只读接口 | 不生成 Version |
| Execution | 无 | 输出数据 | 不直接改 Core |

---

## 十、关于跨层需求的处理机制

若出现跨层需求（例如：

- 编译希望在 HardwareState 中新增字段；
- 预测模块希望将概率写入 Version）：

必须：

1. 提交架构讨论；
2. 评估是否违反核心不变量；
3. 优先考虑扩展层实现；
4. 禁止因单一应用需求修改核心语义。

---

## 十一、禁止的结构性错误

以下情况被视为严重结构错误：

- Core 依赖 intelligence；
- Domain 修改 HardwareState 内部字段；
- Application 绕过 Snapshot；
- 引入循环依赖；
- 在 Core 中添加应用特定逻辑。

---

## 十二、总结

EGM 的结构稳定性依赖于：

- 单向依赖；
- 严格分层；
- 不变量保护；
- 禁止跨层修改。

模块依赖纪律，是平台长期演化的前提条件。

任何违反本文件原则的修改，应被视为架构层问题，而非实现层问题。