"""
SuiteLifecycleManager

统一管理 Suite 生命周期：

- 状态机（CREATED → RUNNING → ANALYZING → COMPLETED）
- 异常捕获
- 执行时间记录
- 日志记录

避免每个 Suite 重复写控制逻辑。
"""