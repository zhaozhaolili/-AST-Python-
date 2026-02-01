#!/usr/bin/env python3

from setuptools import setup, find_packages
import os

# 读取README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取版本
version = {}
with open("pyanalyzer/__init__.py", "r", encoding="utf-8") as fh:
    exec(fh.read(), version)

# 读取依赖
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pyanalyzer",
    version=version.get("__version__", "1.0.0"),
    author="开源软件基础课程小组",
    author_email="example@university.edu",
    description="基于AST与符号执行的Python代码缺陷检测工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pyanalyzer",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    package_data={
        "pyanalyzer": [
            "config.yaml",
            "templates/*",
            "data/*",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pyanalyzer=pyanalyzer.cli:cli",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "coverage>=6.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.900",
            "pre-commit>=2.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
    },
    keywords=[
        "static-analysis",
        "code-quality",
        "python",
        "ast",
        "symbolic-execution",
        "defect-detection",
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/pyanalyzer/issues",
        "Source": "https://github.com/yourusername/pyanalyzer",
        "Documentation": "https://github.com/yourusername/pyanalyzer#readme",
    },
)