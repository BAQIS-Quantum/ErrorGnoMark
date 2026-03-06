# execution/__init__.py
"""
1. Execution 不定义实验逻辑。
2. Execution 不解释物理含义。
3. Backend 只能通过 JobManager 调用。



egm.execution

Execution Layer — 运行控制与任务调度层。

本层负责：

    - 将 Experiment 转换为可提交的运行任务
    - 控制任务调度与并发
    - 与 backend 交互
    - 管理 job 生命周期
    - 聚合运行结果

----------------------------------------
分层职责
----------------------------------------

experiments 负责：
    - 定义实验协议
    - 构造电路
    - 定义参数扫描
    - 解释数据

execution 负责：
    - 任务拆分
    - 批量提交
    - 调度控制
    - 运行时异常处理
    - 结果聚合

foundation.backends 负责：
    - 平台 API 适配
    - 提供 submit / status / fetch 接口

domain 负责：
    - 误差推断
    - 误差建模
    - 误差传播与分析

----------------------------------------
依赖方向（必须遵守）
----------------------------------------

execution 可以依赖：
    - experiments
    - foundation.backends
    - schemas

execution 不得依赖：
    - domain
    - analysis
    - reporting
    - suites

----------------------------------------
重要设计原则
----------------------------------------

1. Execution 不定义实验逻辑。
2. Execution 不解释误差含义。
3. Execution 仅负责“如何运行”。
4. 所有 backend 交互必须通过 job_manager。
5. 所有批量控制必须通过 scheduler。
6. 不允许在 suites 中直接调用 backend。

----------------------------------------
一句话总结
----------------------------------------

Execution 是运行时控制系统。
它不决定测什么，只决定如何跑。
suites
   ↓
experiments
   ↓
execution
   ↓
foundation.backends
   ↓
hardware / simulator


✅ backend 抽象清晰
✅ execution 不污染 experiment
✅ suites 不污染 execution
✅ domain 完全隔离
✅ 可替换 backend
✅ 可替换 scheduler
✅ 支持规模化
✅ 支持云端
✅ 支持本地模拟


Execution Layer

本模块负责“运行控制”。

它解决的问题是：

    如何把 Experiment 跑起来。

它不解决：

    - 测什么（experiments）
    - 误差是什么（domain）
    - 数据如何解释（analysis）
    - 结果如何展示（reporting）

----------------------------------------
核心职责
----------------------------------------

1. 任务拆分
2. 调度控制
3. backend 调用
4. job 生命周期管理
5. 结果聚合

----------------------------------------
依赖方向
----------------------------------------

允许依赖：
    - experiments
    - foundation.backends
    - schemas

禁止依赖：
    - domain
    - analysis
    - reporting
    - suites

----------------------------------------
架构原则
----------------------------------------

Execution 是运行时系统。
它永远不定义实验逻辑。




""""""
Runtime 子模块

本目录存放 execution 的运行时辅助组件：

    - 状态追踪
    - 重试策略
    - 结果聚合

这些模块是 execution 的内部实现细节。
不应被 experiments 或 suites 直接调用。
"""