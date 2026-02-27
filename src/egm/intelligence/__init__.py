# """
# The Core Sub-package of ErrorGnoMark.

# This sub-package contains the fundamental building blocks of the EGM framework,
# as defined in the V3 architecture. It includes circuits, experiments,
# analysis tools, and backend abstractions.

# This __init__.py file selectively exposes the most important classes
# at the `errorgnomark.core` level for easier user access, using relative imports
# for internal modularity.
# """

# # 从 'circuits' 模块中提升关键类
# # 路径: errorgnomark/core/circuits/circuit.py
# from .circuits.circuit import QuantumCircuit

# # 从 'experiments' 模块中提升实验基类和一些代表性实验
# # 路径: errorgnomark/core/experiments/base.py  <-- 已修正这里的路径
# from .experiments.base import Experiment
# # 路径: errorgnomark/core/experiments/benchmarking/rb.py
# from .experiments.benchmarking.rb import StandardRBExperiment
# # 路径: errorgnomark/core/experiments/characterization/incoherent/t1.py
# from .experiments.characterization.incoherent.t1 import T1Experiment
# # 路径: errorgnomark/core/experiments/tomography/qpt.py (根据文档是qpt.py)
# from .experiments.tomography.qpt import ProcessTomography

# # 从 'analysis' 模块提升核心工具 (如果需要)
# # 路径: errorgnomark/core/analysis/fitting.py
# from .analysis.fitting import Fitter

# # 从 'backends' 模块提升工厂函数
# # 路径: errorgnomark/core/backends/__init__.py
# from .backends import get_backend

# # 使用 __all__ 定义 `from egm.core import *` 时应导出的公共API
# __all__ = [
#     # 来自 circuits
#     "QuantumCircuit",

#     # 来自 experiments
#     "Experiment",
#     "StandardRBExperiment",
#     "T1Experiment",
#     "ProcessTomography",

#     # 来自 analysis
#     "Fitter",

#     # 来自 backends
#     "get_backend",
# ]