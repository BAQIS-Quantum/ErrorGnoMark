"""
error_modeling 模块

语义定位：
    单门误差建模层（Microscopic Error Modeling）

核心作用：
    将 ResultSchema 转化为结构化的 GateErrorModel，
    建立“单门误差的参数化表达”。

解决的问题：
    - 每个 gate 的 error rate 是多少？
    - 误差是否可分解为不同物理成分？
    - 如何用统一参数结构表达误差？

输入：
    ResultSchema

输出：
    GateErrorModel

典型内容：
    - 单门 error budget
    - 参数化误差结构
    - 误差分量拆解

依赖关系：
    ✅ 依赖 egm.schemas
    ✅ 依赖 domain.models
    ❌ 不依赖 error_inference
    ❌ 不依赖 error_propagation

边界约束：
    - 只处理“单门层级”语义
    - 不做跨实验推理
    - 不做 logical error 推导
"""