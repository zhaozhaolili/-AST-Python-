"""
代码指标计算
"""

import ast
import math
from typing import Dict, List, Any, Tuple


def calculate_metrics(source_code: str) -> Dict[str, Any]:
    """计算代码指标"""
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return {}
    
    # 基本指标
    lines = source_code.split('\n')
    total_lines = len(lines)
    non_empty_lines = len([line for line in lines if line.strip()])
    comment_lines = len([line for line in lines if line.strip().startswith('#')])
    
    # 统计节点
    function_count = len([node for node in ast.walk(tree) 
                         if isinstance(node, ast.FunctionDef)])
    class_count = len([node for node in ast.walk(tree) 
                      if isinstance(node, ast.ClassDef)])
    import_count = len([node for node in ast.walk(tree) 
                       if isinstance(node, (ast.Import, ast.ImportFrom))])
    
    # 计算平均函数长度和复杂度
    function_metrics = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start_line = node.lineno
            end_line = getattr(node, 'end_lineno', start_line)
            length = end_line - start_line + 1 if end_line else 10
            
            complexity = calculate_complexity(node)
            
            function_metrics.append({
                'name': node.name,
                'length': length,
                'complexity': complexity,
                'line': start_line
            })
    
    avg_function_length = 0
    avg_complexity = 0
    if function_metrics:
        avg_function_length = sum(f['length'] for f in function_metrics) / len(function_metrics)
        avg_complexity = sum(f['complexity'] for f in function_metrics) / len(function_metrics)
    
    # 计算Halstead指标
    halstead = calculate_halstead_metrics(tree)
    
    # 计算可维护性指数
    maintainability = calculate_maintainability_index(
        halstead.get('volume', 0),
        avg_complexity,
        total_lines
    )
    
    return {
        'total_lines': total_lines,
        'non_empty_lines': non_empty_lines,
        'comment_lines': comment_lines,
        'comment_ratio': comment_lines / total_lines if total_lines > 0 else 0,
        'function_count': function_count,
        'class_count': class_count,
        'import_count': import_count,
        'avg_function_length': avg_function_length,
        'avg_cyclomatic_complexity': avg_complexity,
        'halstead_metrics': halstead,
        'maintainability_index': maintainability,
        'function_metrics': function_metrics
    }


def calculate_complexity(node: ast.AST) -> int:
    """计算圈复杂度"""
    complexity = 1
    
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, (ast.Try, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.Match):
            complexity += len(child.cases)
    
    return complexity


def calculate_halstead_metrics(tree: ast.AST) -> Dict[str, float]:
    """计算Halstead指标"""
    operators = set()
    operands = set()
    operator_count = 0
    operand_count = 0
    
    # 定义操作符和操作数
    operator_keywords = {
        '+', '-', '*', '/', '//', '%', '**',  # 算术
        '==', '!=', '<', '<=', '>', '>=',  # 比较
        'and', 'or', 'not',  # 逻辑
        'is', 'is not', 'in', 'not in',  # 身份/成员
        '&', '|', '^', '~', '<<', '>>',  # 位运算
        '=', '+=', '-=', '*=', '/=', '//=', '%=', '**=',  # 赋值
        '&=', '|=', '^=', '<<=', '>>=',  # 位赋值
    }
    
    for node in ast.walk(tree):
        # 统计操作符
        if isinstance(node, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
                           ast.Mod, ast.Pow, ast.LShift, ast.RShift,
                           ast.BitOr, ast.BitXor, ast.BitAnd, ast.MatMult)):
            operators.add(type(node).__name__)
            operator_count += 1
        
        elif isinstance(node, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE,
                             ast.Gt, ast.GtE, ast.Is, ast.IsNot,
                             ast.In, ast.NotIn)):
            operators.add(type(node).__name__)
            operator_count += 1
        
        elif isinstance(node, (ast.And, ast.Or, ast.Not)):
            operators.add(type(node).__name__)
            operator_count += 1
        
        # 统计操作数（变量和常量）
        elif isinstance(node, ast.Name):
            operands.add(node.id)
            operand_count += 1
        
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, str, bool)):
                operands.add(str(node.value))
                operand_count += 1
    
    # 计算Halstead指标
    n1 = len(operators)  # 独特操作符数
    n2 = len(operands)   # 独特操作数数
    N1 = operator_count  # 操作符总数
    N2 = operand_count   # 操作数总数
    
    # 避免除以零
    if n1 == 0 or n2 == 0:
        return {
            'vocabulary': 0,
            'length': 0,
            'volume': 0,
            'difficulty': 0,
            'effort': 0,
            'time': 0,
            'bugs': 0
        }
    
    vocabulary = n1 + n2
    length = N1 + N2
    volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
    difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
    effort = difficulty * volume
    time = effort / 18  # 假设每秒18个基本决策
    bugs = volume / 3000  # 每3000个基本单位一个bug
    
    return {
        'vocabulary': vocabulary,
        'length': length,
        'volume': volume,
        'difficulty': difficulty,
        'effort': effort,
        'time': time,
        'bugs': bugs
    }


def calculate_maintainability_index(volume: float, 
                                   complexity: float, 
                                   lines: int) -> float:
    """计算可维护性指数"""
    if lines == 0:
        return 100.0
    
    # 原始公式: MI = 171 - 5.2 * ln(V) - 0.23 * (C) - 16.2 * ln(LOC)
    # 简化版本
    try:
        mi = 171 - 5.2 * math.log(volume + 1) - 0.23 * complexity - 16.2 * math.log(lines)
        return max(0, min(100, mi))
    except (ValueError, ZeroDivisionError):
        return 50.0


def calculate_code_churn(old_code: str, new_code: str) -> Dict[str, int]:
    """计算代码变更率"""
    old_lines = old_code.split('\n')
    new_lines = new_code.split('\n')
    
    # 简化的变更计算（实际应该用diff算法）
    added = len([line for line in new_lines if line not in old_lines])
    deleted = len([line for line in old_lines if line not in new_lines])
    modified = min(added, deleted)  # 简化
    
    total_churn = added + deleted + modified
    
    return {
        'added': added,
        'deleted': deleted,
        'modified': modified,
        'total_churn': total_churn,
        'churn_rate': total_churn / len(new_lines) if new_lines else 0
    }


def calculate_test_coverage(metrics: Dict, test_metrics: Dict) -> Dict[str, float]:
    """计算测试覆盖率"""
    if not metrics or not test_metrics:
        return {}
    
    # 计算函数覆盖率
    functions = metrics.get('function_count', 0)
    test_functions = test_metrics.get('function_count', 0)
    function_coverage = test_functions / functions if functions > 0 else 0
    
    # 计算行覆盖率
    lines = metrics.get('total_lines', 0)
    test_lines = test_metrics.get('total_lines', 0)
    line_coverage = test_lines / lines if lines > 0 else 0
    
    # 计算复杂度覆盖率
    complexity = metrics.get('avg_cyclomatic_complexity', 0)
    test_complexity = test_metrics.get('avg_cyclomatic_complexity', 0)
    complexity_coverage = test_complexity / complexity if complexity > 0 else 0
    
    return {
        'function_coverage': function_coverage * 100,
        'line_coverage': line_coverage * 100,
        'complexity_coverage': complexity_coverage * 100,
        'overall_coverage': (function_coverage + line_coverage + complexity_coverage) / 3 * 100
    }


def calculate_technical_debt(metrics: Dict, defects: List[Dict]) -> Dict[str, Any]:
    """计算技术债务"""
    if not metrics:
        return {}
    
    # 基于缺陷计算债务
    defect_debt = 0
    for defect in defects:
        severity = defect.get('severity', 'medium')
        
        # 严重程度权重
        weights = {
            'critical': 10,
            'high': 5,
            'medium': 2,
            'low': 1
        }
        
        defect_debt += weights.get(severity, 1)
    
    # 基于复杂度计算债务
    complexity = metrics.get('avg_cyclomatic_complexity', 0)
    complexity_debt = max(0, complexity - 10) * 2
    
    # 基于函数长度计算债务
    func_length = metrics.get('avg_function_length', 0)
    length_debt = max(0, func_length - 30) * 0.5
    
    total_debt = defect_debt + complexity_debt + length_debt
    
    # 估算修复时间（小时）
    estimated_hours = total_debt * 0.5
    
    return {
        'defect_debt': defect_debt,
        'complexity_debt': complexity_debt,
        'length_debt': length_debt,
        'total_debt': total_debt,
        'estimated_hours': estimated_hours,
        'debt_density': total_debt / metrics.get('total_lines', 1) * 1000
    }