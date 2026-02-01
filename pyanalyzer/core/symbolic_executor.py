"""
符号执行引擎
"""

import ast
import z3
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from z3 import Solver, Int, Real, Bool, And, Or, Not, Implies, sat, unsat, unknown

from pyanalyzer.core.ast_parser import ASTParser
from pyanalyzer.patterns.base_patterns import Defect, Severity


@dataclass
class SymbolicVariable:
    """符号变量"""
    name: str
    z3_var: z3.ExprRef
    type: str  # 'int', 'float', 'bool', 'string'


class SymbolicExecutor:
    """符号执行引擎"""
    
    def __init__(self, parser: ASTParser, max_depth: int = 10):
        self.parser = parser
        self.max_depth = max_depth
        self.solver = Solver()
        self.variables: Dict[str, SymbolicVariable] = {}
        self.path_constraints = []
        self.defects: List[Defect] = []
        
    def analyze(self) -> List[Defect]:
        """执行符号分析"""
        self.defects = []
        
        # 对每个函数进行符号执行
        for func_info in self.parser.functions:
            if func_info.body:
                self._analyze_function(func_info)
        
        return self.defects
    
    def _analyze_function(self, func_info):
        """分析单个函数"""
        # 为函数参数创建符号变量
        for arg_name in func_info.args:
            self._create_symbolic_variable(arg_name, 'int')  # 简化：假设所有参数都是整数
        
        # 遍历函数体
        self._traverse_ast(func_info.body, depth=0)
        
        # 检查路径约束
        self._check_path_constraints()
        
        # 重置状态
        self.variables.clear()
        self.path_constraints.clear()
        self.solver.reset()
    
    def _create_symbolic_variable(self, name: str, var_type: str) -> SymbolicVariable:
        """创建符号变量"""
        if var_type == 'int':
            z3_var = Int(name)
        elif var_type == 'float':
            z3_var = Real(name)
        elif var_type == 'bool':
            z3_var = Bool(name)
        else:
            z3_var = Int(name)  # 默认
        
        var = SymbolicVariable(name=name, z3_var=z3_var, type=var_type)
        self.variables[name] = var
        return var
    
    def _traverse_ast(self, node: ast.AST, depth: int):
        """遍历AST节点"""
        if depth > self.max_depth:
            return
        
        if isinstance(node, ast.If):
            self._analyze_if_statement(node, depth)
        elif isinstance(node, ast.While):
            self._analyze_while_loop(node, depth)
        elif isinstance(node, ast.Assign):
            self._analyze_assignment(node)
        elif isinstance(node, ast.BinOp):
            self._analyze_binary_operation(node)
        elif isinstance(node, ast.Compare):
            self._analyze_comparison(node)
    
    def _analyze_if_statement(self, node: ast.If, depth: int):
        """分析if语句"""
        # 解析条件
        condition = self._parse_expression(node.test)
        if condition:
            # then分支
            self.path_constraints.append(condition)
            for stmt in node.body:
                self._traverse_ast(stmt, depth + 1)
            self.path_constraints.pop()
            
            # else分支（如果有）
            if node.orelse:
                self.path_constraints.append(Not(condition))
                for stmt in node.orelse:
                    self._traverse_ast(stmt, depth + 1)
                self.path_constraints.pop()
    
    def _analyze_while_loop(self, node: ast.While, depth: int):
        """分析while循环"""
        # 解析循环条件
        condition = self._parse_expression(node.test)
        if condition:
            # 循环体（最多执行一次以避免无限展开）
            self.path_constraints.append(condition)
            for stmt in node.body[:3]:  # 只分析前几条语句
                self._traverse_ast(stmt, depth + 1)
            self.path_constraints.pop()
    
    def _analyze_assignment(self, node: ast.Assign):
        """分析赋值语句"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                value = self._parse_expression(node.value)
                
                if value and var_name in self.variables:
                    # 添加约束：变量等于值
                    constraint = (self.variables[var_name].z3_var == value)
                    self.path_constraints.append(constraint)
    
    def _analyze_binary_operation(self, node: ast.BinOp):
        """分析二元运算"""
        left = self._parse_expression(node.left)
        right = self._parse_expression(node.right)
        
        if left is None or right is None:
            return None
        
        op_type = type(node.op)
        
        if op_type == ast.Add:
            return left + right
        elif op_type == ast.Sub:
            return left - right
        elif op_type == ast.Mult:
            return left * right
        elif op_type == ast.Div:
            # 检查除以零
            self._check_division_by_zero(right, node.lineno)
            return left / right
        elif op_type == ast.Eq:
            return left == right
        elif op_type == ast.NotEq:
            return left != right
        elif op_type == ast.Lt:
            return left < right
        elif op_type == ast.LtE:
            return left <= right
        elif op_type == ast.Gt:
            return left > right
        elif op_type == ast.GtE:
            return left >= right
        elif op_type == ast.And:
            return And(left, right)
        elif op_type == ast.Or:
            return Or(left, right)
        
        return None
    
    def _parse_expression(self, node: ast.AST):
        """解析表达式为Z3表达式"""
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
        elif isinstance(node, ast.Name):
            if node.id in self.variables:
                return self.variables[node.id].z3_var
        elif isinstance(node, ast.BinOp):
            return self._analyze_binary_operation(node)
        elif isinstance(node, ast.Compare):
            return self._analyze_comparison(node)
        elif isinstance(node, ast.BoolOp):
            return self._analyze_boolean_operation(node)
        elif isinstance(node, ast.UnaryOp):
            return self._analyze_unary_operation(node)
        
        return None
    
    def _analyze_comparison(self, node: ast.Compare):
        """分析比较运算"""
        if len(node.ops) != 1 or len(node.comparators) != 1:
            return None
        
        left = self._parse_expression(node.left)
        right = self._parse_expression(node.comparators[0])
        
        if left is None or right is None:
            return None
        
        op_type = type(node.ops[0])
        
        if op_type == ast.Eq:
            return left == right
        elif op_type == ast.NotEq:
            return left != right
        elif op_type == ast.Lt:
            return left < right
        elif op_type == ast.LtE:
            return left <= right
        elif op_type == ast.Gt:
            return left > right
        elif op_type == ast.GtE:
            return left >= right
        
        return None
    
    def _analyze_boolean_operation(self, node: ast.BoolOp):
        """分析布尔运算"""
        values = [self._parse_expression(v) for v in node.values]
        values = [v for v in values if v is not None]
        
        if not values:
            return None
        
        if isinstance(node.op, ast.And):
            result = values[0]
            for v in values[1:]:
                result = And(result, v)
            return result
        elif isinstance(node.op, ast.Or):
            result = values[0]
            for v in values[1:]:
                result = Or(result, v)
            return result
        
        return None
    
    def _analyze_unary_operation(self, node: ast.UnaryOp):
        """分析一元运算"""
        operand = self._parse_expression(node.operand)
        if operand is None:
            return None
        
        if isinstance(node.op, ast.USub):
            return -operand
        elif isinstance(node.op, ast.Not):
            return Not(operand)
        
        return None
    
    def _check_division_by_zero(self, divisor, line: int):
        """检查除以零"""
        # 尝试证明除数不可能为零
        self.solver.push()
        
        # 添加当前路径约束
        for constraint in self.path_constraints:
            self.solver.add(constraint)
        
        # 添加除数等于零的约束
        self.solver.add(divisor == 0)
        
        # 检查是否可满足
        result = self.solver.check()
        
        if result == sat:
            # 存在路径使得除数为零
            self.defects.append(Defect(
                pattern="division_by_zero_symbolic",
                description="符号执行发现可能的除以零",
                severity=Severity.HIGH,
                line=line,
                file_path=self.parser.file_path,
                suggestion="添加除数非零检查"
            ))
        
        self.solver.pop()
    
    def _check_path_constraints(self):
        """检查路径约束"""
        # 检查约束是否可满足
        for constraint in self.path_constraints:
            self.solver.add(constraint)
        
        result = self.solver.check()
        
        if result == unsat:
            # 路径不可达
            self.defects.append(Defect(
                pattern="unreachable_code",
                description="符号执行发现不可达代码",
                severity=Severity.MEDIUM,
                line=0,
                file_path=self.parser.file_path,
                suggestion="检查逻辑条件是否矛盾"
            ))
        
        self.solver.reset()
    
    def find_test_inputs(self, func_name: str) -> Dict[str, Any]:
        """为函数生成测试输入"""
        test_inputs = {}
        
        func = self.parser.get_function_by_name(func_name)
        if not func:
            return test_inputs
        
        # 为每个路径生成输入
        for i in range(3):  # 生成最多3组输入
            self.solver.reset()
            
            # 添加路径约束
            for constraint in self.path_constraints[:i+1]:
                self.solver.add(constraint)
            
            if self.solver.check() == sat:
                model = self.solver.model()
                inputs = {}
                
                for var_name, var in self.variables.items():
                    if var_name in func.args:
                        z3_var = var.z3_var
                        if z3_var in model:
                            value = model[z3_var]
                            inputs[var_name] = value
                
                if inputs:
                    test_inputs[f"path_{i+1}"] = inputs
        
        return test_inputs