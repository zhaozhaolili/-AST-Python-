"""
PyAnalyzer - Python静态代码分析工具
"""

__version__ = "1.0.0"
__author__ = "开源软件基础课程小组"
__description__ = "基于AST与符号执行的Python代码缺陷检测工具"

from pyanalyzer.cli import cli

__all__ = ["cli", "__version__"]