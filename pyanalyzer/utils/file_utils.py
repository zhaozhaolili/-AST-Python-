"""
文件工具函数
"""

import os
import fnmatch
from pathlib import Path
from typing import List, Set, Dict


def find_python_files(root_path: str, ignore_config: Dict) -> List[str]:
    """
    查找Python文件，支持忽略模式
    
    Args:
        root_path: 根目录路径
        ignore_config: 忽略配置
        
    Returns:
        找到的Python文件列表
    """
    python_files = []
    root = Path(root_path)
    
    # 获取忽略模式
    ignore_patterns = ignore_config.get("files", [])
    ignore_patterns.extend([
        "__pycache__",
        ".git",
        ".vscode",
        ".idea",
        "venv",
        "env",
        "node_modules",
        "dist",
        "build"
    ])
    
    # 遍历目录
    for file_path in root.rglob("*.py"):
        file_str = str(file_path)
        
        # 检查是否应该忽略
        should_ignore = False
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(file_str, pattern) or pattern in file_str:
                should_ignore = True
                break
        
        if not should_ignore:
            python_files.append(file_str)
    
    return python_files


def read_file_safely(file_path: str, encoding: str = 'utf-8') -> str:
    """
    安全读取文件，处理编码问题
    
    Args:
        file_path: 文件路径
        encoding: 编码
        
    Returns:
        文件内容
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        encodings = ['utf-8-sig', 'gbk', 'gb2312', 'latin-1']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise ValueError(f"无法解码文件: {file_path}")


def is_test_file(file_path: str) -> bool:
    """
    检查是否为测试文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为测试文件
    """
    filename = Path(file_path).name
    return (filename.startswith('test_') or 
            filename.endswith('_test.py') or
            '_test' in filename)


def get_file_size(file_path: str) -> int:
    """
    获取文件大小（字节）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（字节）
    """
    return os.path.getsize(file_path)


def count_lines_in_file(file_path: str) -> int:
    """
    计算文件行数
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件行数
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def create_output_directory(output_path: str) -> Path:
    """
    创建输出目录
    
    Args:
        output_path: 输出目录路径
        
    Returns:
        创建的目录路径
    """
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    获取相对路径
    
    Args:
        file_path: 文件路径
        base_path: 基础路径
        
    Returns:
        相对路径
    """
    return os.path.relpath(file_path, base_path)


def write_json_file(data: dict, file_path: str, indent: int = 2):
    """
    写入JSON文件
    
    Args:
        data: 数据
        file_path: 文件路径
        indent: 缩进
    """
    import json
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def read_json_file(file_path: str) -> dict:
    """
    读取JSON文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        JSON数据
    """
    import json
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)