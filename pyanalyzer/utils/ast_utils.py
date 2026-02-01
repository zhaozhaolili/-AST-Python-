"""
AST工具函数
"""

import ast
from typing import Dict, List, Set, Optional, Any


class ASTWalker:
    """AST遍历器"""
    
    def __init__(self, tree: ast.AST):
        self.tree = tree
    
    def walk(self, node_type: type = None):
        """遍历AST节点"""
        for node in ast.walk(self.tree):
            if node_type is None or isinstance(node, node_type):
                yield node
    
    def find_all(self, node_type: type) -> List[ast.AST]:
        """查找所有指定类型的节点"""
        return list(self.walk(node_type))
    
    def find_first(self, node_type: type) -> Optional[ast.AST]:
        """查找第一个指定类型的节点"""
        for node in self.walk(node_type):
            return node
        return None


class ASTVisitor(ast.NodeVisitor):
    """AST访问器"""
    
    def __init__(self):
        self.nodes = []
        self.parents = {}
        
    def visit(self, node: ast.AST):
        """访问节点"""
        self.nodes.append(node)
        
        # 为子节点设置父节点
        for child in ast.iter_child_nodes(node):
            self.parents[child] = node
        
        # 继续遍历
        self.generic_visit(node)
    
    def get_parent(self, node: ast.AST) -> Optional[ast.AST]:
        """获取父节点"""
        return self.parents.get(node)
    
    def get_ancestors(self, node: ast.AST) -> List[ast.AST]:
        """获取所有祖先节点"""
        ancestors = []
        current = node
        
        while current in self.parents:
            current = self.parents[current]
            ancestors.append(current)
        
        return ancestors
    
    def is_in_function(self, node: ast.AST) -> bool:
        """检查节点是否在函数中"""
        ancestors = self.get_ancestors(node)
        return any(isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef)) 
                  for ancestor in ancestors)
    
    def is_in_class(self, node: ast.AST) -> bool:
        """检查节点是否在类中"""
        ancestors = self.get_ancestors(node)
        return any(isinstance(ancestor, ast.ClassDef) for ancestor in ancestors)


def get_node_position(node: ast.AST) -> Dict[str, int]:
    """获取节点位置信息"""
    position = {
        'lineno': getattr(node, 'lineno', 0),
        'col_offset': getattr(node, 'col_offset', 0),
    }
    
    # 尝试获取结束位置
    if hasattr(node, 'end_lineno'):
        position['end_lineno'] = node.end_lineno
    if hasattr(node, 'end_col_offset'):
        position['end_col_offset'] = node.end_col_offset
    
    return position


def get_function_scope(node: ast.AST) -> Optional[str]:
    """获取节点所在的函数作用域"""
    visitor = ASTVisitor()
    visitor.visit(node)
    
    ancestors = visitor.get_ancestors(node)
    for ancestor in ancestors:
        if isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return ancestor.name
    
    return None


def get_variable_usage(tree: ast.AST) -> Dict[str, Dict[str, List[int]]]:
    """获取变量使用情况"""
    definitions = {}
    references = {}
    
    visitor = ASTVisitor()
    visitor.visit(tree)
    
    for node in visitor.nodes:
        if isinstance(node, ast.Assign):
            # 变量定义
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    if var_name not in definitions:
                        definitions[var_name] = []
                    definitions[var_name].append(node.lineno)
        
        elif isinstance(node, ast.Name):
            # 变量引用
            var_name = node.id
            if isinstance(node.ctx, ast.Load):
                if var_name not in references:
                    references[var_name] = []
                references[var_name].append(node.lineno)
    
    return {
        'definitions': definitions,
        'references': references
    }


def extract_string_constants(tree: ast.AST) -> List[Dict[str, Any]]:
    """提取字符串常量"""
    strings = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.append({
                'value': node.value,
                'line': node.lineno,
                'col_offset': getattr(node, 'col_offset', 0),
                'length': len(node.value)
            })
    
    return strings


def count_node_types(tree: ast.AST) -> Dict[str, int]:
    """统计节点类型"""
    counts = {}
    
    for node in ast.walk(tree):
        node_type = type(node).__name__
        counts[node_type] = counts.get(node_type, 0) + 1
    
    return counts


def get_import_statements(tree: ast.AST) -> List[Dict[str, Any]]:
    """获取导入语句"""
    imports = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    'type': 'import',
                    'module': alias.name,
                    'alias': alias.asname,
                    'line': node.lineno
                })
        
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.append({
                    'type': 'import_from',
                    'module': node.module,
                    'name': alias.name,
                    'alias': alias.asname,
                    'level': node.level,
                    'line': node.lineno
                })
    
    return imports


def get_function_complexity(func_node: ast.FunctionDef) -> Dict[str, Any]:
    """获取函数复杂度信息"""
    complexity = 1  # 起点为1
    
    control_flow_nodes = {
        'if': 0,
        'for': 0,
        'while': 0,
        'try': 0,
        'except': 0,
        'match': 0
    }
    
    for node in ast.walk(func_node):
        if isinstance(node, ast.If):
            complexity += 1
            control_flow_nodes['if'] += 1
        elif isinstance(node, ast.For):
            complexity += 1
            control_flow_nodes['for'] += 1
        elif isinstance(node, ast.While):
            complexity += 1
            control_flow_nodes['while'] += 1
        elif isinstance(node, ast.Try):
            complexity += 1
            control_flow_nodes['try'] += 1
        elif isinstance(node, ast.ExceptHandler):
            complexity += 1
            control_flow_nodes['except'] += 1
        elif isinstance(node, ast.Match):
            complexity += len(node.cases)
            control_flow_nodes['match'] += len(node.cases)
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    
    # 计算嵌套深度
    max_depth = 0
    current_depth = 0
    
    for node in ast.walk(func_node):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 重置深度（新函数）
            current_depth = 0
    
    return {
        'cyclomatic': complexity,
        'max_nesting': max_depth,
        'control_flow': control_flow_nodes
    }


def find_unreachable_code(tree: ast.AST) -> List[Dict[str, Any]]:
    """查找不可达代码"""
    unreachable = []
    
    # 查找return/raise/break/continue之后的代码
    for node in ast.walk(tree):
        if isinstance(node, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
            # 检查同一作用域内是否有后续语句
            parent = None
            for child in ast.walk(tree):
                if child is node:
                    parent = child
                    break
            
            if parent:
                # 这里简化处理，实际需要更复杂的分析
                pass
    
    return unreachable


def validate_syntax(source_code: str) -> Optional[str]:
    """验证语法有效性"""
    try:
        ast.parse(source_code)
        return None
    except SyntaxError as e:
        return f"语法错误: {e.msg} (行{e.lineno}, 列{e.offset})"