"""
模式匹配引擎
负责将AST节点与缺陷模式进行匹配
"""

import ast
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

from pyanalyzer.patterns.base_patterns import Defect, Severity, PATTERNS
from pyanalyzer.patterns.security_patterns import SECURITY_PATTERNS
from pyanalyzer.patterns.performance_patterns import PERFORMANCE_PATTERNS


@dataclass
class PatternMatch:
    """模式匹配结果"""
    pattern_name: str
    node: ast.AST
    context: Dict[str, Any]
    confidence: float = 1.0


class PatternMatcher:
    """模式匹配引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.patterns = {}
        self._load_patterns()
        
    def _load_patterns(self):
        """加载所有模式"""
        # 合并所有模式
        self.patterns.update(PATTERNS)
        self.patterns.update(SECURITY_PATTERNS)
        self.patterns.update(PERFORMANCE_PATTERNS)
        
    def match_all(self, parser, enabled_patterns: List[str] = None) -> List[PatternMatch]:
        """匹配所有模式"""
        matches = []
        
        if enabled_patterns is None:
            enabled_patterns = list(self.patterns.keys())
        
        # 遍历AST树
        for node in ast.walk(parser.ast_tree):
            for pattern_name in enabled_patterns:
                if pattern_name not in self.patterns:
                    continue
                    
                pattern = self.patterns[pattern_name]
                
                try:
                    # 调用检测器
                    detector = pattern['detector']
                    result = detector(node, parser.file_path, parser)
                    
                    if result:
                        matches.append(PatternMatch(
                            pattern_name=pattern_name,
                            node=node,
                            context={
                                'severity': pattern['severity'],
                                'description': pattern['description'],
                                'detector_result': result
                            }
                        ))
                        
                except Exception as e:
                    # 跳过有错误的检测器
                    continue
        
        return matches
    
    def get_pattern_info(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """获取模式信息"""
        if pattern_name in self.patterns:
            pattern = self.patterns[pattern_name]
            return {
                'name': pattern_name,
                'description': pattern.get('description', ''),
                'severity': pattern.get('severity'),
                'category': self._get_pattern_category(pattern_name)
            }
        return None
    
    def _get_pattern_category(self, pattern_name: str) -> str:
        """获取模式分类"""
        if pattern_name in PATTERNS:
            return 'basic'
        elif pattern_name in SECURITY_PATTERNS:
            return 'security'
        elif pattern_name in PERFORMANCE_PATTERNS:
            return 'performance'
        return 'other'
    
    def categorize_matches(self, matches: List[PatternMatch]) -> Dict[str, List[PatternMatch]]:
        """按类别分类匹配结果"""
        categorized = defaultdict(list)
        
        for match in matches:
            category = self._get_pattern_category(match.pattern_name)
            categorized[category].append(match)
        
        return dict(categorized)
    
    def filter_by_severity(self, matches: List[PatternMatch], 
                          min_severity: Severity = Severity.LOW) -> List[PatternMatch]:
        """按严重程度过滤匹配"""
        filtered = []
        
        for match in matches:
            pattern_info = self.get_pattern_info(match.pattern_name)
            if pattern_info and pattern_info['severity']:
                if self._get_severity_value(pattern_info['severity']) >= self._get_severity_value(min_severity):
                    filtered.append(match)
        
        return filtered
    
    def _get_severity_value(self, severity: Severity) -> int:
        """获取严重程度数值"""
        severity_map = {
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4
        }
        return severity_map.get(severity, 0)
    
    def generate_pattern_summary(self, matches: List[PatternMatch]) -> Dict[str, Any]:
        """生成模式统计摘要"""
        summary = {
            'total_matches': len(matches),
            'by_category': defaultdict(int),
            'by_severity': defaultdict(int),
            'by_pattern': defaultdict(int),
            'files_affected': set(),
            'lines_affected': set()
        }
        
        for match in matches:
            pattern_info = self.get_pattern_info(match.pattern_name)
            
            # 按类别统计
            category = self._get_pattern_category(match.pattern_name)
            summary['by_category'][category] += 1
            
            # 按严重程度统计
            if pattern_info and pattern_info['severity']:
                severity = pattern_info['severity'].value
                summary['by_severity'][severity] += 1
            
            # 按模式统计
            summary['by_pattern'][match.pattern_name] += 1
            
            # 记录受影响的行
            if hasattr(match.node, 'lineno'):
                summary['lines_affected'].add(match.node.lineno)
        
        # 转换为常规字典
        summary['by_category'] = dict(summary['by_category'])
        summary['by_severity'] = dict(summary['by_severity'])
        summary['by_pattern'] = dict(summary['by_pattern'])
        
        return summary
    
    def suggest_fixes(self, match: PatternMatch) -> List[str]:
        """为匹配的模式提供修复建议"""
        pattern_name = match.pattern_name
        suggestions = []
        
        # 根据模式提供具体的修复建议
        if pattern_name == 'null_dereference':
            suggestions = [
                "添加空值检查：if obj is not None:",
                "使用安全导航操作符（Python 3.8+）：obj?.attribute",
                "提供默认值：obj.attr if obj else default_value"
            ]
        
        elif pattern_name == 'resource_leak':
            suggestions = [
                "使用with语句自动管理资源：with open('file.txt') as f:",
                "确保在finally块中关闭资源",
                "使用上下文管理器包装资源"
            ]
        
        elif pattern_name == 'sql_injection':
            suggestions = [
                "使用参数化查询：cursor.execute('SELECT * FROM users WHERE name = ?', (name,))",
                "使用ORM框架（如SQLAlchemy）",
                "对用户输入进行严格的验证和转义"
            ]
        
        elif pattern_name == 'hardcoded_password':
            suggestions = [
                "将密码移到环境变量中：os.getenv('PASSWORD')",
                "使用配置文件（如JSON、YAML）",
                "使用密钥管理服务（如AWS Secrets Manager）"
            ]
        
        elif pattern_name == 'division_by_zero':
            suggestions = [
                "添加除数检查：if divisor != 0:",
                "使用try-except捕获ZeroDivisionError",
                "提供默认值或合理的错误处理"
            ]
        
        elif pattern_name == 'long_function':
            suggestions = [
                "将函数拆分为多个更小的函数",
                "提取重复代码为辅助函数",
                "考虑使用类来组织相关功能"
            ]
        
        elif pattern_name == 'high_complexity':
            suggestions = [
                "减少条件分支的数量",
                "使用策略模式替换复杂的条件逻辑",
                "将复杂逻辑提取到单独的函数中"
            ]
        
        else:
            suggestions = ["重构代码以提高可读性和可维护性"]
        
        return suggestions
    
    def validate_pattern_config(self, enabled_patterns: List[str]) -> Tuple[List[str], List[str]]:
        """验证模式配置"""
        valid = []
        invalid = []
        
        for pattern_name in enabled_patterns:
            if pattern_name in self.patterns:
                valid.append(pattern_name)
            else:
                invalid.append(pattern_name)
        
        return valid, invalid