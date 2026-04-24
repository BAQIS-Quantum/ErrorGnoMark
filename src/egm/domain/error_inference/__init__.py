"""
error_inference 模块

语义定位：
    跨实验误差结构归因层（Mesoscopic Inference Layer）

核心作用：
    从多个 GateErrorModel 中，
    推断更高层次的误差结构假设。

解决的问题：
    - 误差是否具有 coherent 成分？
    - stochastic 与 coherent 如何分解？
    - 哪种噪声模型最符合观测数据？
    - 多实验结果是否支持同一假设？

输入：
    List[GateErrorModel]

输出：
    StructuredNoiseHypothesis

典型能力：
    - coherent / stochastic 分解
    - hypothesis ranking
    - 误差结构一致性判断

依赖关系：
    ✅ 依赖 error_modeling 输出
    ✅ 依赖 models
    ❌ 不依赖 error_propagation
    ❌ 不访问 backend 或实验层

边界约束：
    - 不做 QEC 阈值比较
    - 不做 logical error 计算
    - 不产生单门模型（那是 modeling 的职责）
"""