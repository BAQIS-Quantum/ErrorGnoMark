"""
AutoCalibrationSuite

全自动周期性校准流程。

流程：
1. 扫描当前健康状态
2. 判断需校准对象
3. 调 execution 运行校准实验
4. 更新 datastore
5. 生成校准报告
"""