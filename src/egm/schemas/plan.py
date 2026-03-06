"""
plan.py

定义任务计划结构（PlanSchema）。

语义：
    描述一个“实验执行计划”的组合结构。

作用：
    - Suites 构造 Campaign
    - 描述多实验组合关系
    - 支持批量提交

与 Config 的区别：
    Config = 单个实验的参数
    Plan   = 多个实验的调度与组织

禁止：
    - 不包含执行逻辑
    - 不包含误差语义
"""