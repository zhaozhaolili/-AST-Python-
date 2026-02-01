#!/usr/bin/env python3
"""
PyAnalyzer - Python静态代码分析工具命令行接口
"""

import os
import sys
import click
import yaml
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from pyanalyzer.core.ast_parser import ASTParser
from pyanalyzer.core.defect_detector import DefectDetector
from pyanalyzer.core.symbolic_executor import SymbolicExecutor
from pyanalyzer.reporting.html_reporter import HTMLReporter
from pyanalyzer.reporting.json_reporter import JSONReporter
from pyanalyzer.reporting.console_reporter import ConsoleReporter
from pyanalyzer.utils.file_utils import find_python_files
from pyanalyzer.utils.metrics import calculate_metrics


@click.group()
def cli():
    """PyAnalyzer - Python静态代码分析工具"""
    pass


@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--config", "-c", default="config.yaml", help="配置文件路径")
@click.option("--output", "-o", default="./reports", help="报告输出目录")
@click.option("--format", "-f", default="html", 
              type=click.Choice(["html", "json", "console"]), 
              help="报告格式")
@click.option("--severity", "-s", default="medium",
              type=click.Choice(["low", "medium", "high", "critical"]),
              help="最低严重级别")
@click.option("--symbolic", is_flag=True, help="启用符号执行分析")
@click.option("--visualize", is_flag=True, help="生成可视化图表")
def analyze(project_path: str, config: str, output: str, format: str, 
            severity: str, symbolic: bool, visualize: bool):
    """分析Python项目代码"""
    start_time = time.time()
    
    # 加载配置
    config_data = load_config(config)
    config_data["reporting"]["format"] = format
    config_data["reporting"]["output_dir"] = output
    config_data["reporting"]["severity_filter"] = severity
    config_data["symbolic_execution"]["enabled"] = symbolic
    
    click.echo(f"🔍 开始分析项目: {project_path}")
    click.echo(f"📝 使用配置文件: {config}")
    
    # 查找Python文件
    py_files = find_python_files(project_path, config_data.get("ignore", {}))
    click.echo(f"📄 找到 {len(py_files)} 个Python文件")
    
    all_defects = []
    all_metrics = []
    
    # 分析每个文件
    with click.progressbar(py_files, label="分析文件中...", length=len(py_files)) as bar:
        for file_path in bar:
            try:
                defects, metrics = analyze_file(file_path, config_data)
                all_defects.extend(defects)
                all_metrics.append(metrics)
            except Exception as e:
                click.echo(f"\n⚠️  分析文件 {file_path} 时出错: {e}", err=True)
    
    # 生成报告
    if all_defects:
        generate_report(all_defects, all_metrics, config_data, visualize)
    else:
        click.echo("🎉 未发现缺陷！")
    
    # 计算项目指标
    project_metrics = calculate_project_metrics(all_metrics)
    display_summary(all_defects, project_metrics, time.time() - start_time)


@cli.command()
@click.argument("pattern_name")
@click.option("--list", "-l", is_flag=True, help="列出所有可用的缺陷模式")
def patterns(pattern_name: str, list: bool):
    """管理缺陷检测模式"""
    from pyanalyzer.patterns.base_patterns import PATTERNS
    
    if list:
        click.echo("📋 可用缺陷模式:")
        for name, pattern in PATTERNS.items():
            click.echo(f"  • {name}: {pattern['description']} (严重性: {pattern['severity']})")
        return
    
    if pattern_name in PATTERNS:
        pattern = PATTERNS[pattern_name]
        click.echo(f"🔍 模式: {pattern_name}")
        click.echo(f"📝 描述: {pattern['description']}")
        click.echo(f"⚠️  严重性: {pattern['severity']}")
        click.echo(f"📊 检测函数: {pattern['detector'].__name__}")
    else:
        click.echo(f"❌ 未找到模式: {pattern_name}", err=True)
        click.echo(f"使用 'patterns --list' 查看所有可用模式")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def visualize(file_path: str):
    """可视化代码结构"""
    from pyanalyzer.reporting.visualizer import CodeVisualizer
    
    visualizer = CodeVisualizer(file_path)
    output_path = visualizer.generate_call_graph()
    click.echo(f"📊 调用图已生成: {output_path}")
    
    ast_output = visualizer.generate_ast_tree()
    click.echo(f"🌳 AST树图已生成: {ast_output}")


def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    default_config = {
        "patterns": {
            "enabled": [],
            "thresholds": {}
        },
        "symbolic_execution": {
            "enabled": False
        },
        "reporting": {
            "format": "html"
        }
    }
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f) or {}
            # 合并配置
            merged = default_config.copy()
            merged.update(user_config)
            return merged
    
    return default_config


def analyze_file(file_path: str, config: Dict) -> tuple:
    """分析单个文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # 解析AST
    parser = ASTParser(source_code, str(file_path))
    
    # 检测缺陷
    detector = DefectDetector(parser, config)
    defects = detector.detect_all()
    
    # 符号执行（如果启用）
    if config.get("symbolic_execution", {}).get("enabled", False):
        symbolic_executor = SymbolicExecutor(parser)
        symbolic_defects = symbolic_executor.analyze()
        defects.extend(symbolic_defects)
    
    # 计算指标
    metrics = parser.calculate_metrics()
    
    return defects, metrics


def generate_report(defects: List, metrics: List, config: Dict, visualize: bool):
    """生成报告"""
    format_type = config["reporting"]["format"]
    output_dir = config["reporting"]["output_dir"]
    
    os.makedirs(output_dir, exist_ok=True)
    
    if format_type == "html":
        reporter = HTMLReporter(defects, metrics, config)
        output_path = reporter.generate(output_dir)
        click.echo(f"📄 HTML报告已生成: {output_path}")
        
    elif format_type == "json":
        reporter = JSONReporter(defects, metrics, config)
        output_path = reporter.generate(output_dir)
        click.echo(f"📄 JSON报告已生成: {output_path}")
        
    else:  # console
        reporter = ConsoleReporter(defects, metrics, config)
        reporter.display()


def calculate_project_metrics(all_metrics: List) -> Dict:
    """计算项目级指标"""
    if not all_metrics:
        return {}
    
    total_lines = sum(m.get("total_lines", 0) for m in all_metrics)
    total_functions = sum(m.get("function_count", 0) for m in all_metrics)
    total_classes = sum(m.get("class_count", 0) for m in all_metrics)
    avg_complexity = sum(m.get("avg_cyclomatic_complexity", 0) for m in all_metrics) / len(all_metrics)
    
    return {
        "total_lines": total_lines,
        "total_functions": total_functions,
        "total_classes": total_classes,
        "avg_complexity": avg_complexity,
        "files_analyzed": len(all_metrics)
    }


def display_summary(defects: List, metrics: Dict, elapsed_time: float):
    """显示分析摘要"""
    click.echo("\n" + "="*50)
    click.echo("📊 分析摘要")
    click.echo("="*50)
    
    # 缺陷统计
    severity_counts = {}
    for defect in defects:
        sev = defect.severity
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    click.echo(f"🔍 发现缺陷总数: {len(defects)}")
    for severity in ["critical", "high", "medium", "low"]:
        count = severity_counts.get(severity, 0)
        if count > 0:
            click.echo(f"  • {severity.upper()}: {count}")
    
    # 项目指标
    if metrics:
        click.echo(f"\n📈 项目指标:")
        click.echo(f"  • 分析文件数: {metrics.get('files_analyzed', 0)}")
        click.echo(f"  • 总代码行数: {metrics.get('total_lines', 0)}")
        click.echo(f"  • 函数数量: {metrics.get('total_functions', 0)}")
        click.echo(f"  • 类数量: {metrics.get('total_classes', 0)}")
        click.echo(f"  • 平均圈复杂度: {metrics.get('avg_complexity', 0):.2f}")
    
    click.echo(f"\n⏱️  耗时: {elapsed_time:.2f}秒")
    click.echo("="*50)


if __name__ == "__main__":
    cli()