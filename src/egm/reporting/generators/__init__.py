# 假设这个文件原来是这样的
# from .terminal_generator import generate_rb_terminal_report
# from .html_generator import HTMLReportGenerator
# __all__ = ["HTMLReportGenerator", "generate_rb_terminal_report"]

# 请将其修改为（注意两个变化点）：
from .terminal_generator import generate_terminal_report  # <--- 变化点 1：修改导入的函数名
from .html_generator import HTMLReportGenerator

__all__ = ["HTMLReportGenerator", "generate_terminal_report"] # <--- 变化点 2：修改 __all__ 列表中的函数名