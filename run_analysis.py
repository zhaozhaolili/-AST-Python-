#!/usr/bin/env python3
"""
PyAnalyzer运行脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from pyanalyzer.cli import analyze


def main():
    """主函数"""
    print("="*60)
    print("PyAnalyzer 静态代码分析工具")
    print("="*60)
    
    # 检查参数
    if len(sys.argv) < 2:
        print("用法: python run_analysis.py <项目路径> [选项]")
        print("示例: python run_analysis.py examples/example_project")
        print("示例: python run_analysis.py . --symbolic --format html")
        return
    
    project_path = sys.argv[1]
    
    # 构建参数
    args = [project_path]
    
    # 添加选项
    if "--symbolic" in sys.argv:
        args.extend(["--symbolic"])
    if "--format" in sys.argv:
        format_index = sys.argv.index("--format")
        if format_index + 1 < len(sys.argv):
            args.extend(["--format", sys.argv[format_index + 1]])
    if "--output" in sys.argv:
        output_index = sys.argv.index("--output")
        if output_index + 1 < len(sys.argv):
            args.extend(["--output", sys.argv[output_index + 1]])
    
    # 运行分析
    try:
        print(f"🔍 开始分析: {project_path}")
        analyze(args)
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


def demo():
    """演示模式"""
    print("🎬 运行演示模式...")
    
    # 分析示例项目
    print("\n1. 分析示例项目:")
    analyze(["examples/example_project", "--format", "console", "--severity", "low"])
    
    # 分析自身
    print("\n2. 分析PyAnalyzer自身代码:")
    analyze([".", "--format", "console", "--severity", "medium"])
    
    print("\n✅ 演示完成！")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()