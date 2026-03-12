"""
EGM – Compilation Module Architectural Contract
================================================

[模块定位]

Compilation 属于系统的“读路径（Read Path）”。

其职责是：
    - 基于 HardwareSnapshot 进行电路变换
    - 构建 CostModel
    - 生成 Physical / Executable Circuit
    - 可按需触发 Benchmark / Profiling 实验以辅助决策

但其核心语义是：

    ✅ 读取世界
    ❌ 不改变世界


------------------------------------------------------------
[允许行为]

Compilation 可以：

1. 读取 HardwareSnapshot（只读）
2. 访问 ChipTopology / CostModel
3. 调用 ErrorAnalysis 提供权重或评估
4. 触发 Benchmark / Profiling 实验
5. 使用实验结果辅助当前编译决策

其中：

Benchmark / Profiling 实验必须满足：
    - 仅用于当前编译过程
    - 不更新 HardwareState
    - 不更新 NoiseModel
    - 不生成新的 Snapshot
    - 不写入系统级持久状态


------------------------------------------------------------
[禁止行为]

Compilation 严禁：

1. 修改 HardwareState
2. 调用 error_inference 更新参数
3. 修改 NoiseModel 并持久化
4. 生成新的 HardwareSnapshot
5. 触发 Calibration 类型流程
6. 直接写入 Datastore 作为系统状态更新


------------------------------------------------------------
[语义边界]

Calibration 改变世界。
Compilation 读取世界。

如果编译过程中检测到硬件质量不足：

    ✅ 可以请求（orchestrate）Calibration
    ❌ 但不能自行修改硬件状态


------------------------------------------------------------
[架构原则]

- Snapshot Isolation 必须保持
- Read / Write Path 必须分离
- HardwareState 的写权限应集中在 suites/calibration
- 所有编译行为应保持可复现性（在相同 Snapshot 下 deterministic）


------------------------------------------------------------
[长期约束]

任何将 Benchmark 结果写回系统状态的行为，
都应迁移至 Calibration 流程，而不是放入 Compilation。

违反上述约束将导致：

    - Snapshot 语义破坏
    - Traceability 混乱
    - 不可复现行为
    - 架构层级退化


------------------------------------------------------------

EGM 是一个 State-Aware、Versioned、Traceable 平台。

请确保：
Compilation 始终保持“观察者”角色，而非“状态修改者”。

"""