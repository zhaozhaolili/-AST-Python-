"""
安全相关的缺陷模式
"""

import ast
import re
from typing import List, Optional
from dataclasses import dataclass

from pyanalyzer.patterns.base_patterns import Defect, Severity


@dataclass
class SecurityPattern:
    """安全模式"""
    name: str
    description: str
    severity: Severity
    detector: callable


class SecurityPatterns:
    """安全缺陷模式"""
    
    @staticmethod
    def detect_unsafe_deserialization(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测不安全的反序列化"""
        defects = []
        
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            unsafe_deserializers = {
                'pickle.loads', 'pickle.load',
                'marshal.loads', 'marshal.load',
                'yaml.load', 'yaml.safe_load',
                'eval', 'exec'
            }
            
            if func_name in unsafe_deserializers:
                defects.append(Defect(
                    pattern="unsafe_deserialization",
                    description=f"使用不安全的反序列化函数: {func_name}",
                    severity=Severity.CRITICAL,
                    line=node.lineno,
                    file_path=file_path,
                    context=ast.unparse(node),
                    suggestion=f"使用安全替代方案，如json.loads()或pickle.HIGHEST_PROTOCOL"
                ))
        
        return defects if defects else None
    
    @staticmethod
    def detect_command_injection(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测命令注入"""
        defects = []
        
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            shell_functions = {'os.system', 'subprocess.call', 'subprocess.Popen', 'os.popen'}
            
            if func_name in shell_functions or func_name in ['system', 'call', 'Popen', 'popen']:
                # 检查参数中是否有用户输入
                for arg in node.args:
                    arg_str = ast.unparse(arg)
                    # 检查是否有字符串拼接或变量
                    if '+' in arg_str or any(char.isalpha() for char in arg_str if char not in ['"', "'", ' ']):
                        defects.append(Defect(
                            pattern="command_injection",
                            description="潜在的命令注入漏洞",
                            severity=Severity.CRITICAL,
                            line=node.lineno,
                            file_path=file_path,
                            context=ast.unparse(node),
                            suggestion="使用subprocess.run()并传递参数列表，避免使用shell=True"
                        ))
                        break
        
        return defects if defects else None
    
    @staticmethod
    def detect_path_traversal(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测路径遍历漏洞"""
        defects = []
        
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            file_functions = {'open', 'os.open', 'os.remove', 'os.rename', 'shutil.copy'}
            
            if func_name in file_functions:
                # 检查参数中是否有用户控制的路径
                if node.args:
                    first_arg = ast.unparse(node.args[0])
                    # 检查是否有相对路径或用户输入
                    if '..' in first_arg or '/' in first_arg or '\\' in first_arg:
                        # 检查是否使用了os.path.join进行安全连接
                        if not SecurityPatterns._is_safe_path_construction(node):
                            defects.append(Defect(
                                pattern="path_traversal",
                                description="潜在的路径遍历漏洞",
                                severity=Severity.HIGH,
                                line=node.lineno,
                                file_path=file_path,
                                context=ast.unparse(node),
                                suggestion="使用os.path.join()和os.path.normpath()处理路径，验证用户输入"
                            ))
        
        return defects if defects else None
    
    @staticmethod
    def _is_safe_path_construction(node: ast.AST) -> bool:
        """检查是否使用安全的路径构建方式"""
        # 检查是否使用了os.path.join
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'join' and isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == 'path' and isinstance(node.func.value.value, ast.Name):
                        if node.func.value.value.id == 'os':
                            return True
        return False
    
    @staticmethod
    def detect_weak_cryptography(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测弱加密算法"""
        defects = []
        
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            weak_algorithms = {
                'md5', 'sha1', 'DES', 'RC4',
                'hashlib.md5', 'hashlib.sha1',
                'Crypto.Cipher.DES', 'Crypto.Cipher.ARC4'
            }
            
            if func_name in weak_algorithms:
                defects.append(Defect(
                    pattern="weak_cryptography",
                    description=f"使用弱加密算法: {func_name}",
                    severity=Severity.HIGH,
                    line=node.lineno,
                    file_path=file_path,
                    context=ast.unparse(node),
                    suggestion="使用强加密算法，如SHA-256、AES-256"
                ))
        
        return defects if defects else None
    
    @staticmethod
    def detect_insecure_random(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测不安全的随机数生成"""
        defects = []
        
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            insecure_random = {'random.random', 'random.randint', 'random.choice'}
            
            if func_name in insecure_random:
                # 检查是否用于安全相关场景
                parent = getattr(node, 'parent', None)
                if parent and isinstance(parent, ast.Assign):
                    for target in parent.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id.lower()
                            security_keywords = {'token', 'key', 'secret', 'password', 'salt'}
                            if any(keyword in var_name for keyword in security_keywords):
                                defects.append(Defect(
                                    pattern="insecure_random",
                                    description="使用不安全的随机数生成器",
                                    severity=Severity.HIGH,
                                    line=node.lineno,
                                    file_path=file_path,
                                    context=ast.unparse(parent),
                                    suggestion="使用secrets模块生成安全随机数"
                                ))
                                break
        
        return defects if defects else None
    
    @staticmethod
    def detect_xxe_vulnerability(node: ast.AST, file_path: str) -> Optional[List[Defect]]:
        """检测XXE漏洞"""
        defects = []
        
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            xml_parsers = {
                'xml.etree.ElementTree.parse', 'xml.etree.ElementTree.fromstring',
                'lxml.etree.parse', 'lxml.etree.fromstring',
                'minidom.parse', 'minidom.parseString'
            }
            
            if func_name in xml_parsers:
                # 检查是否禁用了外部实体
                # 这里简化检查，实际需要更复杂的分析
                defects.append(Defect(
                    pattern="potential_xxe",
                    description="XML解析可能未禁用外部实体",
                    severity=Severity.HIGH,
                    line=node.lineno,
                    file_path=file_path,
                    context=ast.unparse(node),
                    suggestion="禁用XML外部实体解析：defusedxml"
                ))
        
        return defects if defects else None


# 安全模式集合
SECURITY_PATTERNS = {
    "unsafe_deserialization": SecurityPattern(
        name="unsafe_deserialization",
        description="不安全的反序列化",
        severity=Severity.CRITICAL,
        detector=SecurityPatterns.detect_unsafe_deserialization
    ),
    "command_injection": SecurityPattern(
        name="command_injection",
        description="命令注入",
        severity=Severity.CRITICAL,
        detector=SecurityPatterns.detect_command_injection
    ),
    "path_traversal": SecurityPattern(
        name="path_traversal",
        description="路径遍历",
        severity=Severity.HIGH,
        detector=SecurityPatterns.detect_path_traversal
    ),
    "weak_cryptography": SecurityPattern(
        name="weak_cryptography",
        description="弱加密算法",
        severity=Severity.HIGH,
        detector=SecurityPatterns.detect_weak_cryptography
    ),
    "insecure_random": SecurityPattern(
        name="insecure_random",
        description="不安全的随机数",
        severity=Severity.HIGH,
        detector=SecurityPatterns.detect_insecure_random
    ),
    "potential_xxe": SecurityPattern(
        name="potential_xxe",
        description="潜在的XXE漏洞",
        severity=Severity.HIGH,
        detector=SecurityPatterns.detect_xxe_vulnerability
    ),
}