"""
AST解析器模块
"""

import ast
import libcst as cst
import astunparse
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    lineno: int
    args: List[str]
    returns: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    body: Optional[ast.AST] = None
    complexity: int = 1


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    lineno: int
    bases: List[str]
    methods: List[FunctionInfo] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)


class ASTParser:
    """抽象语法树解析器"""
    
    def __init__(self, source_code: str, file_path: str = ""):
        self.source_code = source_code
        self.file_path = file_path
        
        # 解析AST
        try:
            self.ast_tree = ast.parse(source_code)
            self.cst_tree = cst.parse_module(source_code)
        except SyntaxError as e:
            raise ValueError(f"语法错误: {e}")
        
        # 提取信息
        self._extract_info()
    
    def _extract_info(self):
        """从AST中提取信息"""
        self.functions = []
        self.classes = []
        self.imports = []
        self.variables = defaultdict(list)
        
        # 遍历AST
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._parse_function(node)
                self.functions.append(func_info)
                
            elif isinstance(node, ast.ClassDef):
                class_info = self._parse_class(node)
                self.classes.append(class_info)
                
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self._parse_import(node)
                self.imports.append(import_info)
                
            elif isinstance(node, ast.Assign):
                self._parse_assignment(node)
    
    def _parse_function(self, node: ast.FunctionDef) -> FunctionInfo:
        """解析函数定义"""
        args = []
        if node.args.args:
            args = [arg.arg for arg in node.args.args]
        
        # 计算圈复杂度
        complexity = self._calculate_cyclomatic_complexity(node)
        
        return FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            args=args,
            returns=ast.unparse(node.returns) if node.returns else None,
            docstring=ast.get_docstring(node),
            decorators=[ast.unparse(decorator) for decorator in node.decorator_list],
            body=node,
            complexity=complexity
        )
    
    def _parse_class(self, node: ast.ClassDef) -> ClassInfo:
        """解析类定义"""
        bases = []
        if node.bases:
            bases = [ast.unparse(base) for base in node.bases]
        
        # 提取类的方法
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(self._parse_function(item))
        
        # 提取类属性
        attributes = []
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
        
        return ClassInfo(
            name=node.name,
            lineno=node.lineno,
            bases=bases,
            methods=methods,
            attributes=attributes
        )
    
    def _parse_import(self, node: ast.AST) -> Dict:
        """解析导入语句"""
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            return {"type": "import", "names": names, "lineno": node.lineno}
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            return {
                "type": "import_from", 
                "module": node.module or "", 
                "names": names, 
                "level": node.level,
                "lineno": node.lineno
            }
    
    def _parse_assignment(self, node: ast.Assign):
        """解析赋值语句"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables[target.id].append(node.lineno)
            elif isinstance(target, ast.Tuple):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.variables[elt.id].append(node.lineno)
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1  # 起始复杂度为1
        
        for child in ast.walk(node):
            # 增加复杂度的节点类型
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # 布尔操作符中的每个运算符增加1
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.Match):
                # match语句的每个case增加1
                complexity += len(child.cases)
        
        return complexity
    
    def get_all_calls(self) -> List[Dict]:
        """获取所有函数调用"""
        calls = []
        
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append({
                        "function": node.func.id,
                        "lineno": node.lineno,
                        "args": len(node.args)
                    })
                elif isinstance(node.func, ast.Attribute):
                    calls.append({
                        "function": node.func.attr,
                        "lineno": node.lineno,
                        "module": ast.unparse(node.func.value),
                        "args": len(node.args)
                    })
        
        return calls
    
    def get_control_flow_nodes(self) -> List[Dict]:
        """获取控制流节点（if/while/for等）"""
        flow_nodes = []
        
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.If):
                flow_nodes.append({
                    "type": "if",
                    "lineno": node.lineno,
                    "test": ast.unparse(node.test) if node.test else "",
                    "has_else": bool(node.orelse)
                })
            elif isinstance(node, ast.While):
                flow_nodes.append({
                    "type": "while",
                    "lineno": node.lineno,
                    "test": ast.unparse(node.test) if node.test else "",
                    "has_else": bool(node.orelse)
                })
            elif isinstance(node, ast.For):
                flow_nodes.append({
                    "type": "for",
                    "lineno": node.lineno,
                    "target": ast.unparse(node.target) if node.target else "",
                    "iter": ast.unparse(node.iter) if node.iter else "",
                    "has_else": bool(node.orelse)
                })
        
        return flow_nodes
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """计算代码指标"""
        total_lines = len(self.source_code.split('\n'))
        function_count = len(self.functions)
        class_count = len(self.classes)
        
        # 计算平均函数长度
        func_lengths = []
        for func in self.functions:
            if func.body:
                # 估算函数行数
                end_lineno = getattr(func.body, 'end_lineno', func.lineno + 10)
                func_lengths.append(end_lineno - func.lineno)
        
        avg_function_length = sum(func_lengths) / len(func_lengths) if func_lengths else 0
        
        # 计算平均圈复杂度
        complexities = [func.complexity for func in self.functions]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 1
        
        # 统计导入数量
        import_count = len(self.imports)
        
        # 统计变量数量
        variable_count = len(self.variables)
        
        return {
            "total_lines": total_lines,
            "function_count": function_count,
            "class_count": class_count,
            "avg_function_length": avg_function_length,
            "avg_cyclomatic_complexity": avg_complexity,
            "import_count": import_count,
            "variable_count": variable_count,
            "file_path": self.file_path
        }
    
    def get_function_by_name(self, name: str) -> Optional[FunctionInfo]:
        """根据名称查找函数"""
        for func in self.functions:
            if func.name == name:
                return func
        return None
    
    def get_class_by_name(self, name: str) -> Optional[ClassInfo]:
        """根据名称查找类"""
        for cls in self.classes:
            if cls.name == name:
                return cls
        return None
    
    def find_unused_variables(self) -> List[Dict]:
        """查找未使用的变量"""
        unused = []
        
        # 获取所有变量使用
        used_vars = set()
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_vars.add(node.id)
        
        # 检查哪些变量定义了但未使用
        for var_name, lines in self.variables.items():
            if var_name not in used_vars:
                # 排除以_开头的变量（通常是有意不使用的）
                if not var_name.startswith('_'):
                    unused.append({
                        "variable": var_name,
                        "lines": lines,
                        "reason": "定义了但未使用"
                    })
        
        return unused
    
    def generate_ast_dump(self) -> str:
        """生成AST的字符串表示"""
        return ast.dump(self.ast_tree, indent=2)