"""schemas/
│
├── __init__.py
├── base.py
├── versioning.py
├── metadata.py
├── configs.py
├── plan.py
│
├── results/
│   ├── __init__.py
│   ├── base.py
│   ├── rb.py
│   ├── prb.py
│   ├── csb.py
│   ├── spb.py
│   ├── tomo.py
│   └── xeb.py
│
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   ├── rb.py
│   ├── prb.py
│   ├── csb.py
│   ├── spb.py
│   ├── tomo.py
│   └── xeb.py
│
└── migration/
    ├── __init__.py
    ├── registry.py
    └── rb_migration.py


egm.schemas

系统运行语言层（System Contract Layer）。

职责：
    - 定义全系统统一的数据契约
    - 为 Experiments、Domain、Suites 提供统一数据结构
    - 提供版本控制与迁移机制

原则：
    - 只定义数据结构
    - 不包含物理解释逻辑
    - 不包含实验执行逻辑
    - 不包含算法实现
    - 不依赖 experiments / domain / suites

系统内部只允许流动 Schema 对象。


schemas
   ├── 不 import experiments
   ├── 不 import domain
   ├── 不 import suites
   └── 不 import reporting


schemas 现在包含 5 个子责任：

结构定义（base / results）
配置定义（configs）
调度定义（plan）
数据入口（adapters）
版本演进（migration


"""







# """
# egm.schemas

# 系统运行语言层（System Contract Layer）

# 定位：
#     定义全系统的数据契约与类型结构。
#     是 Experiments、Domain、Suites 之间的唯一通信语言。

# 核心原则：
#     - 只定义数据结构
#     - 不包含算法逻辑
#     - 不包含推理逻辑
#     - 不包含执行逻辑
#     - 不访问 backend
#     - 不 import domain
#     - 不 import experiments

# 它不是业务模块。
# 它是“系统语言定义层”。




# schemas/
#     __init__.py

#     base.py                # 基础 Schema 抽象
#     configs.py             # 实验配置结构
#     plan.py                # 任务计划结构

#     results/
#         __init__.py
#         base.py            # 通用 ResultSchema
#         rb.py
#         prb.py
#         csb.py
#         spb.py
#         tomo.py
#         xeb.py


#  依赖方向：

# Experiments ─────▶ schemas
# Domain ───────────▶ schemas
# Suites ───────────▶ schemas
# Reporting ────────▶ schemas

# schemas 不依赖任何业务模块。  



# 类型	作用
# ConfigSchema	实验输入参数
# PlanSchema	多实验组织结构
# ResultSchema	实验输出数据
# MetadataSchema	版本与追踪
# BaseSchema	序列化基类

# 所有 Schema 必须可 JSON 序列化
# 所有 ResultSchema 必须包含 config_snapshot
# Schema 不允许包含方法逻辑（只允许轻量 validation）
# Schema 版本必须可演进（version 字段）
# 不允许 domain 修改 ResultSchema


# schemas = 系统运行语言

# domain = 解释数据
# experiments = 生成数据
# suites = 组织数据
# execution = 执行数据
# reporting = 展示数据
# schemas 是它们之间唯一的“语法”。
# """