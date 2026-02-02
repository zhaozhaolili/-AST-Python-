# 🔍 PyAnalyzer - Python静态代码分析工具

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![GitHub Actions](https://github.com/zhaozhaolili/-AST-Python-/workflows/PyAnalyzer%20Code%20Analysis/badge.svg)
![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-brightgreen)

基于AST与符号执行的Python代码缺陷检测工具，《开源软件基础》课程大作业项目。

## ✨ 特性

- **AST解析**: 使用Python标准库`ast`和`libcst`解析代码
- **缺陷检测**: 内置多种常见代码缺陷模式
- **符号执行**: 集成Z3求解器进行路径约束分析
- **智能报告**: 生成详细的HTML/JSON/控制台报告
- **可视化**: 代码结构、调用图、缺陷分布可视化
- **可扩展**: 支持自定义缺陷检测模式

## 📦 安装

### 从源码安装
```bash
git clone https://github.com/zhaozhaolili/-AST-python-.git
cd pyanalyzer
pip install -r requirements.txt
pip install -e .

pyanalyzer/
├── pyanalyzer/
│   ├── __init__.py
│   ├── cli.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ast_parser.py
│   │   ├── defect_detector.py
│   │   ├── pattern_matcher.py
│   │   ├── symbolic_executor.py
│   │   └── call_graph.py
│   ├── patterns/
│   │   ├── __init__.py
│   │   ├── base_patterns.py
│   │   ├── security_patterns.py
│   │   └── performance_patterns.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_utils.py
│   │   ├── ast_utils.py
│   │   └── metrics.py
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── html_reporter.py
│   │   ├── json_reporter.py
│   │   ├── console_reporter.py
│   │   └── visualizer.py
│   └── tests/
│       ├── __init__.py
│       └── test_core.py
├── examples/
│   ├── example_project/
│   │   ├── __init__.py
│   │   ├── vulnerable_code.py
│   │   └── complex_logic.py
│   └── test_cases.py
├── requirements.txt
├── setup.py
├── pyproject.toml
├── README.md
├── config.yaml
└── .gitignore
