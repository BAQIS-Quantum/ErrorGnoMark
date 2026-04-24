"""
error_propagation 模块

语义定位：
    跨层误差传播层（Macroscopic Error Projection）

核心作用：
    将物理误差模型投影到 logical 层，
    评估容错能力与阈值关系。

解决的问题：
    - 给定物理误差，logical error rate 是多少？
    - 是否低于 QEC threshold？
    - 各误差分量对 logical failure 的贡献是多少？
    - 如何分配 error budget？

输入：
    StructuredNoiseHypothesis
    或 GateErrorModel

输出：
    LogicalErrorEstimate
    ErrorBudgetReport

典型能力：
    - 物理误差 → logical error 映射
    - QEC 阈值比较
    - error budget 分配分析

依赖关系：
    ✅ 依赖 error_inference
    ✅ 依赖 theory
    ❌ 不依赖 experiments
    ❌ 不控制实验

边界约束：
    - 不做误差结构拟合
    - 不做 hypothesis ranking
    - 只做传播与阈值分析
"""