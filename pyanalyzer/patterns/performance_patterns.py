"""
性能相关的缺陷模式
"""

import ast
from typing import List, Optional
from dataclasses import dataclass

from pyanalyzer.patterns.base_patterns import Defect, Severity


@dataclass
class PerformancePattern:
    """性能模式"""
    name: str
    description: str
    severity: Severity
    detector: callable


class PerformancePatterns:
    """性能缺陷模式"""
    
    @staticmethod
    def detect_nested_loops(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测嵌套循环"""
        defects = []
        
        def count_nested_loops(node: ast.AST, depth: int = 0):
            """递归计算嵌套深度"""
            if isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
                depth += 1
                if depth >= 3:  # 超过3层嵌套
                    defects.append(Defect(
                        pattern="deep_nested_loops",
                        description=f"深度嵌套循环（{depth}层）",
                        severity=Severity.MEDIUM,
                        line=node.lineno,
                        file_path=file_path,
                        context=ast.unparse(node),
                        suggestion="考虑重构以减少嵌套深度，使用函数提取"
                    ))
            
            for child in ast.iter_child_nodes(node):
                count_nested_loops(child, depth)
        
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            count_nested_loops(node)
        
        return defects if defects else None
    
    @staticmethod
    def detect_string_concatenation_in_loop(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测循环中的字符串拼接"""
        defects = []
        
        if isinstance(node, ast.For):
            # 检查循环体中是否有字符串拼接
            for stmt in node.body:
                if isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.Add):
                    if isinstance(stmt.target, ast.Name):
                        defects.append(Defect(
                            pattern="string_concat_in_loop",
                            description="循环中使用字符串拼接",
                            severity=Severity.MEDIUM,
                            line=node.lineno,
                            file_path=file_path,
                            context=ast.unparse(node),
                            suggestion="使用列表和join()方法"
                        ))
                        break
        
        return defects if defects else None
    
    @staticmethod
    def detect_unnecessary_computation(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测不必要的重复计算"""
        defects = []
        
        if isinstance(node, ast.For):
            # 查找循环中可能被提取的常量计算
            loop_invariants = set()
            
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    # 检查赋值是否依赖循环变量
                    deps = PerformancePatterns._get_dependencies(stmt.value)
                    if not deps:
                        # 不依赖循环变量，可能可以提到循环外
                        loop_invariants.update([target.id for target in stmt.targets 
                                              if isinstance(target, ast.Name)])
            
            if loop_invariants:
                defects.append(Defect(
                    pattern="loop_invariant_code",
                    description=f"循环中不变的计算: {', '.join(loop_invariants)}",
                    severity=Severity.LOW,
                    line=node.lineno,
                    file_path=file_path,
                    context=ast.unparse(node),
                    suggestion="将不依赖循环变量的计算移到循环外部"
                ))
        
        return defects if defects else None
    
    @staticmethod
    def _get_dependencies(node: ast.AST) -> set:
        """获取表达式的依赖变量"""
        deps = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                deps.add(child.id)
        
        return deps
    
    @staticmethod
    def detect_large_list_comprehension(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测过大的列表推导式"""
        defects = []
        
        if isinstance(node, ast.ListComp):
            # 计算推导式的复杂度
            generators = node.generators
            if len(generators) > 2:  # 超过2层生成器
                defects.append(Defect(
                    pattern="complex_list_comprehension",
                    description="复杂的列表推导式",
                    severity=Severity.LOW,
                    line=node.lineno,
                    file_path=file_path,
                    context=ast.unparse(node),
                    suggestion="考虑使用普通循环以提高可读性"
                ))
        
        return defects if defects else None
    
    @staticmethod
    def detect_global_variable_access(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测频繁访问的全局变量"""
        defects = []
        
        if isinstance(node, ast.FunctionDef):
            global_accesses = 0
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                    # 检查是否访问全局变量
                    # 简化检查：假设所有非局部变量都是全局的
                    if child.id not in [arg.arg for arg in node.args.args]:
                        global_accesses += 1
            
            if global_accesses > 5:  # 频繁访问全局变量
                defects.append(Defect(
                    pattern="frequent_global_access",
                    description="函数频繁访问全局变量",
                    severity=Severity.LOW,
                    line=node.lineno,
                    file_path=file_path,
                    context=node.name,
                    suggestion="将频繁访问的全局变量作为参数传递或缓存到局部变量"
                ))
        
        return defects if defects else None
    
    @staticmethod
    def detect_inefficient_data_structure(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测低效的数据结构使用"""
        defects = []
        
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            # 检查列表的in操作（O(n)）
            if func_name == 'in' and isinstance(node.func, ast.Name):
                # 检查左侧是否为列表
                if len(node.args) > 0 and isinstance(node.args[0], ast.List):
                    defects.append(Defect(
                        pattern="inefficient_membership_test",
                        description="在列表中使用in操作符（O(n)）",
                        severity=Severity.MEDIUM,
                        line=node.lineno,
                        file_path=file_path,
                        context=ast.unparse(node),
                        suggestion="考虑使用集合（set）或字典进行成员测试（O(1)）"
                    ))
        
        return defects if defects else None
    
    @staticmethod
    def detect_copy_instead_of_view(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测不必要的拷贝"""
        defects = []
        
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            copy_functions = {'copy', 'deepcopy', 'list', '[:]'}
            
            if func_name in copy_functions:
                # 检查是否真的需要拷贝
                parent = getattr(node, 'parent', None)
                if parent and isinstance(parent, ast.For):
                    # 循环中拷贝可能是不必要的
                    defects.append(Defect(
                        pattern="unnecessary_copy",
                        description="可能不必要的拷贝操作",
                        severity=Severity.LOW,
                        line=node.lineno,
                        file_path=file_path,
                        context=ast.unparse(node),
                        suggestion="考虑使用视图（切片）而不是拷贝"
                    ))
        
        return defects if defects else None


# 性能模式集合
PERFORMANCE_PATTERNS = {
    "deep_nested_loops": PerformancePattern(
        name="deep_nested_loops",
        description="深度嵌套循环",
        severity=Severity.MEDIUM,
        detector=PerformancePatterns.detect_nested_loops
    ),
    "string_concat_in_loop": PerformancePattern(
        name="string_concat_in_loop",
        description="循环中字符串拼接",
        severity=Severity.MEDIUM,
        detector=PerformancePatterns.detect_string_concatenation_in_loop
    ),
    "loop_invariant_code": PerformancePattern(
        name="loop_invariant_code",
        description="循环中不变的计算",
        severity=Severity.LOW,
        detector=PerformancePatterns.detect_unnecessary_computation
    ),
    "complex_list_comprehension": PerformancePattern(
        name="complex_list_comprehension",
        description="复杂的列表推导式",
        severity=Severity.LOW,
        detector=PerformancePatterns.detect_large_list_comprehension
    ),
    "frequent_global_access": PerformancePattern(
        name="frequent_global_access",
        description="频繁访问全局变量",
        severity=Severity.LOW,
        detector=PerformancePatterns.detect_global_variable_access
    ),
    "inefficient_membership_test": PerformancePattern(
        name="inefficient_membership_test",
        description="低效的成员测试",
        severity=Severity.MEDIUM,
        detector=PerformancePatterns.detect_inefficient_data_structure
    ),
    "unnecessary_copy": PerformancePattern(
        name="unnecessary_copy",
        description="不必要的拷贝",
        severity=Severity.LOW,
        detector=PerformancePatterns.detect_copy_instead_of_view
    ),
}