"""
configs.py

定义实验配置结构（Experiment Configuration Schema）。

语义：
    描述“要做什么实验”，
    不描述“实验如何执行”。

作用：
    - Experiments 的输入
    - Suites 构造实验时使用
    - execution 层调度参数来源

内容示例：
    - backend_name
    - shots
    - qubits
    - gate_set
    - noise_flags

注意：
    ConfigSchema 只描述参数，不包含执行结果。
"""