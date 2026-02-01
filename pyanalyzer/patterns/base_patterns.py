"""
基础缺陷检测模式
"""

import ast
import re
from typing import Dict, List, Any, Callable, Optional
from enum import Enum
from dataclasses import dataclass


class Severity(Enum):
    """缺陷严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Defect:
    """缺陷信息"""
    pattern: str
    description: str
    severity: Severity
    line: int
    file_path: str
    context: Optional[str] = None
    suggestion: Optional[str] = None


# 缺陷检测器函数类型
DetectorFunc = Callable[[ast.AST, str, 'ASTParser'], Optional[List[Defect]]]


class BasePatterns:
    """基础缺陷检测模式"""
    
    @staticmethod
    def detect_null_dereference(node: ast.AST, file_path: str, parser: 'ASTParser') -> Optional[List[Defect]]:
        """检测空指针解引用"""
        defects = []
        
        if isinstance(node, ast.Attribute):
            # 检查 obj.attr 中的 obj 是否为 None
            value = ast.unparse(node.value)
            if value == 'None':
                defects.append(Defect(
                    pattern="null_dereference",
                    description="访问None对象的属性",
                    severity=Severity.HIGH,
                    line=node.lineno,
                    file_path=file_path,
                    context=ast.unparse(node),
                    suggestion=f"在访问属性前检查 {value} 是否为None"
                ))
        
        elif isinstance(node, ast.Subscript):
            # 检查 container[index] 中的 container 是否为 None
            value = ast.unparse(node.value)
            if value == 'None':
                defects.append(Defect(
                    pattern="null_dereference",
                    description="访问None对象的元素",
                    severity=Severity.HIGH,
                    line=node.lineno,
                    file_path=file_path,
                    context=ast.unparse(node),
                    suggestion=f"在访问元素前检查 {value} 是否为None"
                ))
        
        elif isinstance(node, ast.Call):
            # 检查 func() 中的 func 是否为 None
            if isinstance(node.func, ast.Name) and node.func.id == 'None':
                defects.append(Defect(
                    pattern="null_dereference",
                    description="调用None对象",
                    severity=Severity.HIGH,
                    line=node.lineno,
                    file_path=file_path,
                    context=ast.unparse(node),
                    suggestion="在调用前检查函数是否为None"
                ))
        
        return defects if defects else None
    
    @staticmethod
    def detect_resource_leak(node: ast.AST, file_path: str, parser: 'ASTParser') -> Optional[List[Defect]]:
        """检测资源泄漏"""
        defects = []
        
        if isinstance(node, ast.With):
            # with语句通常会自动关闭资源
            return None
        
        if isinstance(node, ast.Call):
            # 检查是否打开了文件但没有关闭
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            resource_functions = {'open', 'connect', 'start', 'create'}
            if func_name in resource_functions:
                # 查找父作用域，检查是否有对应的关闭操作
                defects.append(Defect(
                    pattern="resource_leak",
                    description=f"可能未正确关闭{func_name}打开的资源",
                    severity=Severity.MEDIUM,
                    line=node.lineno,
                    file_path=file_path,
                    context=ast.unparse(node),
                    suggestion=f"使用with语句或确保调用close()方法"
                ))
        
        return defects if defects else None
    
    @staticmethod
    def detect_unused_variable(node: ast.AST, file_path: str, parser: 'ASTParser') -> Optional[List[Defect]]:
        """检测未使用的变量"""
        # 这个检测在ASTParser中实现更高效
        return None
    
    @staticmethod
    def detect_division_by_zero(node: ast.AST, file_path: str, parser: 'ASTParser') -> Optional[List[Defect]]:
        """检测除以零"""
        defects = []
        
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            # 检查除数是否为0
            right_expr = ast.unparse(node.right)
            if right_expr == '0' or right_expr == '0.0':
                defects.append(Defect(
                    pattern="division_by_zero",
                    description="除以零",
                    severity=Severity.HIGH,
                    line=node.lineno,
                    file_path=file_path,
                    context=ast.unparse(node),
                    suggestion="检查除数是否可能为零"
                ))
        
        return defects if defects else None
    
    @staticmethod
    def detect_hardcoded_password(node: ast.AST, file_path: str, parser: 'ASTParser') -> Optional[List[Defect]]:
        """检测硬编码的密码"""
        defects = []
        
        # 检查字符串中是否包含密码
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value.lower()
            
            # 密码相关关键词
            password_keywords = {
                'password', 'passwd', 'pwd', 'secret', 'key',
                'token', 'auth', 'credential', 'apikey', 'apisecret'
            }
            
            # 检查变量名或上下文
            parent = getattr(node, 'parent', None)
            if parent and isinstance(parent, ast.Assign):
                for target in parent.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        for keyword in password_keywords:
                            if keyword in var_name:
                                defects.append(Defect(
                                    pattern="hardcoded_password",
                                    description="发现硬编码的密码/密钥",
                                    severity=Severity.CRITICAL,
                                    line=node.lineno,
                                    file_path=file_path,
                                    context=ast.unparse(parent),
                                    suggestion="使用环境变量或配置文件存储敏感信息"
                                ))
                                break
        
        return defects if defects else None
    
    @staticmethod
    def detect_sql_injection(node: ast.AST, file_path: str, parser: 'ASTParser') -> Optional[List[Defect]]:
        """检测SQL注入漏洞"""
        defects = []
        
        if isinstance(node, ast.Call):
            # 检查是否使用字符串拼接构建SQL
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            sql_functions = {'execute', 'executemany', 'query', 'raw'}
            db_modules = {'sqlite3', 'psycopg2', 'mysql', 'pymysql'}
            
            if func_name in sql_functions:
                # 检查参数中是否有字符串拼接
                for arg in node.args:
                    arg_str = ast.unparse(arg)
                    if '+' in arg_str or '%' in arg_str or 'format(' in arg_str:
                        defects.append(Defect(
                            pattern="sql_injection",
                            description="潜在的SQL注入漏洞",
                            severity=Severity.CRITICAL,
                            line=node.lineno,
                            file_path=file_path,
                            context=ast.unparse(node),
                            suggestion="使用参数化查询或ORM"
                        ))
        
        return defects if defects else None
    
    @staticmethod
    def detect_infinite_loop(node: ast.AST, file_path: str, parser: 'ASTParser') -> Optional[List[Defect]]:
        """检测无限循环"""
        defects = []
        
        if isinstance(node, ast.While):
            # 检查while条件是否为常量True
            test = ast.unparse(node.test)
            if test == 'True' or test == '1':
                defects.append(Defect(
                    pattern="potential_loop_infinite",
                    description="可能无限循环",
                    severity=Severity.MEDIUM,
                    line=node.lineno,
                    file_path=file_path,
                    context=ast.unparse(node),
                    suggestion="确保循环有终止条件或添加超时机制"
                ))
        
        return defects if defects else None
    
    @staticmethod
    def detect_missing_type_hints(node: ast.AST, file_path: str, parser: 'ASTParser') -> Optional[List[Defect]]:
        """检测缺少类型注解"""
        defects = []
        
        if isinstance(node, ast.FunctionDef):
            # 检查函数是否有返回类型注解
            if not node.returns:
                defects.append(Defect(
                    pattern="missing_type_hints",
                    description="函数缺少返回类型注解",
                    severity=Severity.LOW,
                    line=node.lineno,
                    file_path=file_path,
                    context=node.name,
                    suggestion=f"添加返回类型注解: def {node.name}(...) -> ReturnType:"
                ))
            
            # 检查参数是否有类型注解
            for arg in node.args.args:
                if not arg.annotation:
                    defects.append(Defect(
                        pattern="missing_type_hints",
                        description=f"参数'{arg.arg}'缺少类型注解",
                        severity=Severity.LOW,
                        line=node.lineno,
                        file_path=file_path,
                        context=node.name,
                        suggestion=f"添加类型注解: {arg.arg}: Type"
                    ))
        
        return defects if defects else None
    
    @staticmethod
    def detect_long_function(node: ast.AST, file_path: str, parser: 'ASTParser', threshold: int = 50) -> Optional[List[Defect]]:
        """检测过长函数"""
        defects = []
        
        if isinstance(node, ast.FunctionDef):
            # 估算函数长度
            start_line = node.lineno
            end_line = getattr(node, 'end_lineno', start_line + 1)
            length = end_line - start_line
            
            if length > threshold:
                defects.append(Defect(
                    pattern="long_function",
                    description=f"函数过长 ({length}行)",
                    severity=Severity.MEDIUM,
                    line=node.lineno,
                    file_path=file_path,
                    context=node.name,
                    suggestion="考虑将函数拆分为更小的函数"
                ))
        
        return defects if defects else None
    
    @staticmethod
    def detect_high_complexity(node: ast.AST, file_path: str, parser: 'ASTParser', threshold: int = 10) -> Optional[List[Defect]]:
        """检测高复杂度函数"""
        defects = []
        
        if isinstance(node, ast.FunctionDef):
            # 在ASTParser中计算复杂度
            func = parser.get_function_by_name(node.name)
            if func and func.complexity > threshold:
                defects.append(Defect(
                    pattern="high_complexity",
                    description=f"函数圈复杂度过高 ({func.complexity})",
                    severity=Severity.MEDIUM,
                    line=node.lineno,
                    file_path=file_path,
                    context=node.name,
                    suggestion="重构函数以降低复杂度"
                ))
        
        return defects if defects else None


# 所有可用的缺陷模式
PATTERNS = {
    "null_dereference": {
        "description": "空指针解引用",
        "severity": Severity.HIGH,
        "detector": BasePatterns.detect_null_dereference
    },
    "resource_leak": {
        "description": "资源泄漏",
        "severity": Severity.MEDIUM,
        "detector": BasePatterns.detect_resource_leak
    },
    "division_by_zero": {
        "description": "除以零",
        "severity": Severity.HIGH,
        "detector": BasePatterns.detect_division_by_zero
    },
    "hardcoded_password": {
        "description": "硬编码密码",
        "severity": Severity.CRITICAL,
        "detector": BasePatterns.detect_hardcoded_password
    },
    "sql_injection": {
        "description": "SQL注入漏洞",
        "severity": Severity.CRITICAL,
        "detector": BasePatterns.detect_sql_injection
    },
    "potential_loop_infinite": {
        "description": "可能无限循环",
        "severity": Severity.MEDIUM,
        "detector": BasePatterns.detect_infinite_loop
    },
    "missing_type_hints": {
        "description": "缺少类型注解",
        "severity": Severity.LOW,
        "detector": BasePatterns.detect_missing_type_hints
    },
    "long_function": {
        "description": "函数过长",
        "severity": Severity.MEDIUM,
        "detector": BasePatterns.detect_long_function
    },
    "high_complexity": {
        "description": "高圈复杂度",
        "severity": Severity.MEDIUM,
        "detector": BasePatterns.detect_high_complexity
    }
}