"""
Schema 版本控制定义。

提供：
    - 全局 SCHEMA_MAJOR_VERSION
    - SCHEMA_MINOR_VERSION
    - 版本兼容性检查工具

用于控制结构破坏性升级。

规则：
    - Major 表示破坏性修改
    - Minor 表示向后兼容新增字段
"""