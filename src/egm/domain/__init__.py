"""
Domain 层 = 误差语义核心层（Error Intelligence Core）

定位：
    将实验数据（ResultSchema）转化为“可解释的误差结构”，
    并进一步推演其对逻辑层与容错能力的影响。

核心职责：
    - 建立误差的结构化表示
    - 做跨实验误差归因
    - 做物理误差 → logical error 的传播推理
    - 提供 error intelligence 输出对象

严格边界：
    ✅ 只依赖 egm.schemas
    ✅ 可依赖内部 models / theory
    ❌ 不依赖 Experiments
    ❌ 不依赖 Suites
    ❌ 不依赖 execution / backend
    ❌ 不控制实验流程

输入：
    ResultSchema

输出：
    GateErrorModel
    StructuredNoiseHypothesis
    LogicalErrorEstimate
    ErrorBudgetReport

依赖方向（不可违反）：

models ─────────────┐
                    ▼
error_modeling ─────▶ error_inference ─────▶ error_propagation
                                             ▲
theory ─────────────────────────────────────┘

Domain ─────▶ egm.schemas

禁止反向依赖。
"""