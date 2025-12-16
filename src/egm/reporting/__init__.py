# 这个文件可能看起来像这样：
# from .generators.terminal_generator import generate_rb_terminal_report
# __all__ = [
#     'generate_rb_terminal_report',
# ]

# 请将其修改为（注意两个变化点）：
from .generators import generate_terminal_report  # <--- 变化点 1：修改导入的函数名和路径

__all__ = [
    'generate_terminal_report', # <--- 变化点 2：修改 __all__ 列表中的函数名
]