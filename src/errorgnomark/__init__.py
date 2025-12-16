"""
ErrorGnoMark (EGM): A Quantum Processor Characterization and Verification Framework.

This is the main entry point of the errorgnomark library, aligned with the V3 architecture.
It defines package-level metadata. Sub-modules and classes should be imported
from their specific paths to maintain architectural clarity.

Example:
    from egm.core.experiments.benchmarking.rb import StandardRBExperiment
    from egm.schemas.plan import ExperimentPlan
"""

# 1. 定义包的元数据
# 这对于版本控制、调试和用户支持至关重要
__version__ = "3.0.0-dev"
__author__ = "Xudan Chai"
__email__ = "chaixd@baqis.ac.cn"
__architecture_version__ = "V3-20231211"
__package_name__ = "errorgnomark"  # 明确声明包名

# 2. 使用 `__all__` 定义顶层包的公共API
# 根据新架构，我们保持顶层命名空间的干净。
# 鼓励用户直接从子包（如 `errorgnomark.core` 或 `errorgnomark.schemas`）导入。
__all__ = [
    # 元数据
    "__version__",
    "__author__",
    "__email__",
    "__architecture_version__",
    "__package_name__",
]

# 注意:
# 在这个新架构中，我们避免用包深处的类来填充顶层命名空间。
# 这强制实施了分层设计，使代码更具可读性和可维护性。
#
# 在新架构下正确的导入方式:
# >>> from egm.core.circuits.circuit import QuantumCircuit
# >>> from egm.core.experiments.benchmarking.rb import StandardRBExperiment
#
# SDK层 (`errorgnomark.sdk`) 将在未来为构建和运行实验提供更友好的高层接口。