"""
BaseSuite

所有 Suite 的抽象基类。

定义统一接口：
- prepare()
- run()
- analyze()
- report()

约束：
- 每个 Suite 必须是可重复执行的完整流程
- 不包含底层物理建模
- 不直接操作 datastore（通过 execution 或 intelligence）
"""


# class BaseSuite:

#     def prepare(self):
#         """准备阶段：加载配置、绑定 backend、初始化资源"""

#     def run(self):
#         """执行阶段：运行主要 workflow"""

#     def analyze(self):
#         """分析阶段：调用 analysis 或 intelligence 生成结果"""

#     def report(self):
#         """输出阶段：生成报告"""