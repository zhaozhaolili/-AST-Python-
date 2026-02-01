"""
缺陷检测器主类
"""

import ast
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from pyanalyzer.core.ast_parser import ASTParser
from pyanalyzer.patterns.base_patterns import PATTERNS, Defect, Severity


class DefectDetector:
    """缺陷检测器"""
    
    def __init__(self, parser: ASTParser, config: Dict[str, Any]):
        self.parser = parser
        self.config = config
        self.enabled_patterns = config.get("patterns", {}).get("enabled", [])
        self.thresholds = config.get("patterns", {}).get("thresholds", {})
        
    def detect_all(self) -> List[Defect]:
        """检测所有缺陷"""
        all_defects = []
        
        # 遍历AST树
        for node in ast.walk(self.parser.ast_tree):
            defects = self._detect_node_defects(node)
            all_defects.extend(defects)
        
        # 特殊检测：未使用变量
        if "unused_variable" in self.enabled_patterns:
            unused_defects = self._detect_unused_variables()
            all_defects.extend(unused_defects)
        
        # 特殊检测：未使用导入
        if "unused_import" in self.enabled_patterns:
            import_defects = self._detect_unused_imports()
            all_defects.extend(import_defects)
        
        # 过滤严重级别
        min_severity = Severity[self.config.get("reporting", {}).get("severity_filter", "medium").upper()]
        filtered_defects = [
            defect for defect in all_defects 
            if self._get_severity_value(defect.severity) >= self._get_severity_value(min_severity)
        ]
        
        return filtered_defects
    
    def _detect_node_defects(self, node: ast.AST) -> List[Defect]:
        """检测单个节点的缺陷"""
        defects = []
        
        for pattern_name in self.enabled_patterns:
            if pattern_name in PATTERNS:
                pattern = PATTERNS[pattern_name]
                detector = pattern["detector"]
                
                try:
                    # 传递阈值参数给需要它的检测器
                    if pattern_name in ["long_function", "high_complexity"]:
                        threshold = self.thresholds.get(
                            "function_length" if pattern_name == "long_function" else "cyclomatic_complexity",
                            50 if pattern_name == "long_function" else 10
                        )
                        result = detector(node, self.parser.file_path, self.parser, threshold)
                    else:
                        result = detector(node, self.parser.file_path, self.parser)
                    
                    if result:
                        defects.extend(result)
                except Exception as e:
                    # 跳过检测器错误
                    continue
        
        return defects
    
    def _detect_unused_variables(self) -> List[Defect]:
        """检测未使用的变量"""
        defects = []
        unused_vars = self.parser.find_unused_variables()
        
        for var_info in unused_vars:
            for line in var_info["lines"]:
                defects.append(Defect(
                    pattern="unused_variable",
                    description=f"变量 '{var_info['variable']}' 定义了但未使用",
                    severity=Severity.LOW,
                    line=line,
                    file_path=self.parser.file_path,
                    context=var_info["variable"],
                    suggestion="删除未使用的变量或添加使用它的代码"
                ))
        
        return defects
    
    def _detect_unused_imports(self) -> List[Defect]:
        """检测未使用的导入"""
        defects = []
        
        # 获取所有使用的名称
        used_names = set()
        for node in ast.walk(self.parser.ast_tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
        
        # 检查导入是否被使用
        for import_info in self.parser.imports:
            if import_info["type"] == "import":
                for name in import_info["names"]:
                    # 检查导入的模块是否被使用
                    if name not in used_names:
                        # 检查是否有别名
                        actual_name = name.split(" as ")[0] if " as " in name else name
                        if actual_name not in used_names:
                            defects.append(Defect(
                                pattern="unused_import",
                                description=f"未使用的导入: {name}",
                                severity=Severity.LOW,
                                line=import_info["lineno"],
                                file_path=self.parser.file_path,
                                context=name,
                                suggestion="删除未使用的导入"
                            ))
            elif import_info["type"] == "import_from":
                for name in import_info["names"]:
                    # 检查导入的名称是否被使用
                    if name not in used_names:
                        defects.append(Defect(
                            pattern="unused_import",
                            description=f"未使用的导入: {name}",
                            severity=Severity.LOW,
                            line=import_info["lineno"],
                            file_path=self.parser.file_path,
                            context=name,
                            suggestion="删除未使用的导入"
                        ))
        
        return defects
    
    def _get_severity_value(self, severity: Severity) -> int:
        """将严重程度转换为数值"""
        severity_values = {
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4
        }
        return severity_values.get(severity, 0)
    
    def get_pattern_statistics(self) -> Dict[str, int]:
        """获取缺陷模式统计"""
        defects = self.detect_all()
        stats = {}
        
        for defect in defects:
            pattern = defect.pattern
            stats[pattern] = stats.get(pattern, 0) + 1
        
        return stats