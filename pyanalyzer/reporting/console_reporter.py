"""
控制台报告生成器
"""

import sys
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from pyanalyzer.patterns.base_patterns import Defect, Severity


class ConsoleReporter:
    """控制台报告生成器"""
    
    def __init__(self, defects: List[Defect], metrics: List[Dict], config: Dict):
        self.defects = defects
        self.metrics = metrics
        self.config = config
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 颜色代码
        self.COLORS = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'underline': '\033[4m',
            'reset': '\033[0m',
        }
        
        # 严重程度颜色映射
        self.SEVERITY_COLORS = {
            Severity.CRITICAL: self.COLORS['red'],
            Severity.HIGH: self.COLORS['magenta'],
            Severity.MEDIUM: self.COLORS['yellow'],
            Severity.LOW: self.COLORS['cyan'],
        }
        
    def display(self):
        """显示报告到控制台"""
        self._print_header()
        self._print_summary()
        self._print_defects_table()
        self._print_metrics()
        self._print_recommendations()
        self._print_footer()
    
    def _print_header(self):
        """打印头部信息"""
        print("\n" + "="*80)
        print(f"{self.COLORS['bold']}{self.COLORS['blue']}🔍 PyAnalyzer 代码分析报告{self.COLORS['reset']}")
        print("="*80)
        print(f"{self.COLORS['cyan']}生成时间: {self.timestamp}{self.COLORS['reset']}")
        print(f"{self.COLORS['cyan']}配置文件: {self.config.get('__file__', '默认配置')}{self.COLORS['reset']}")
        print("-"*80)
    
    def _print_summary(self):
        """打印摘要信息"""
        severity_counts = self._count_defects_by_severity()
        total_defects = len(self.defects)
        
        print(f"\n{self.COLORS['bold']}📊 分析摘要{self.COLORS['reset']}")
        print("-"*40)
        
        # 缺陷统计
        print(f"{self.COLORS['white']}分析文件数: {len(self.metrics)}{self.COLORS['reset']}")
        print(f"{self.COLORS['white']}发现缺陷总数: {total_defects}{self.COLORS['reset']}")
        
        if total_defects > 0:
            for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    color = self.SEVERITY_COLORS.get(severity, self.COLORS['white'])
                    severity_name = severity.value.upper()
                    print(f"  {color}● {severity_name}: {count}{self.COLORS['reset']}")
        
        # 质量评分
        quality_score = self._calculate_quality_score()
        quality_color = self.COLORS['green']
        if quality_score < 60:
            quality_color = self.COLORS['red']
        elif quality_score < 80:
            quality_color = self.COLORS['yellow']
        
        print(f"\n{self.COLORS['bold']}📈 质量评分: {quality_color}{quality_score:.1f}/100{self.COLORS['reset']}")
        
        if total_defects == 0:
            print(f"\n{self.COLORS['green']}✅ 恭喜！未发现代码缺陷。{self.COLORS['reset']}")
    
    def _print_defects_table(self):
        """打印缺陷表格"""
        if not self.defects:
            return
        
        print(f"\n{self.COLORS['bold']}🔎 缺陷详情{self.COLORS['reset']}")
        print("-"*80)
        
        # 按文件分组缺陷
        defects_by_file = {}
        for defect in self.defects:
            file_path = defect.file_path
            if file_path not in defects_by_file:
                defects_by_file[file_path] = []
            defects_by_file[file_path].append(defect)
        
        # 打印每个文件的缺陷
        for file_path, defects in defects_by_file.items():
            file_name = Path(file_path).name
            print(f"\n{self.COLORS['underline']}{self.COLORS['white']}{file_name}{self.COLORS['reset']}")
            
            for defect in defects:
                self._print_defect(defect)
    
    def _print_defect(self, defect: Defect):
        """打印单个缺陷"""
        severity_color = self.SEVERITY_COLORS.get(defect.severity, self.COLORS['white'])
        
        # 缺陷标题
        severity_str = defect.severity.value.upper()
        print(f"\n  {severity_color}[{severity_str}]{self.COLORS['reset']} {defect.pattern}")
        
        # 缺陷详情
        print(f"     {self.COLORS['yellow']}位置: {defect.file_path}:{defect.line}{self.COLORS['reset']}")
        print(f"     {self.COLORS['white']}描述: {defect.description}{self.COLORS['reset']}")
        
        if defect.context:
            # 截断过长的上下文
            context = defect.context
            if len(context) > 100:
                context = context[:97] + "..."
            print(f"     {self.COLORS['cyan']}上下文: {context}{self.COLORS['reset']}")
        
        if defect.suggestion:
            print(f"     {self.COLORS['green']}建议: {defect.suggestion}{self.COLORS['reset']}")
    
    def _print_metrics(self):
        """打印代码指标"""
        if not self.metrics:
            return
        
        print(f"\n{self.COLORS['bold']}📏 代码指标{self.COLORS['reset']}")
        print("-"*40)
        
        # 计算总体指标
        total_lines = sum(m.get("total_lines", 0) for m in self.metrics)
        total_functions = sum(m.get("function_count", 0) for m in self.metrics)
        total_classes = sum(m.get("class_count", 0) for m in self.metrics)
        
        # 计算平均复杂度
        complexities = [m.get("avg_cyclomatic_complexity", 0) 
                       for m in self.metrics if m.get("avg_cyclomatic_complexity", 0) > 0]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        
        print(f"{self.COLORS['white']}总代码行数: {total_lines}{self.COLORS['reset']}")
        print(f"{self.COLORS['white']}函数数量: {total_functions}{self.COLORS['reset']}")
        print(f"{self.COLORS['white']}类数量: {total_classes}{self.COLORS['reset']}")
        
        # 复杂度评估
        complexity_color = self.COLORS['green']
        if avg_complexity > 15:
            complexity_color = self.COLORS['red']
        elif avg_complexity > 10:
            complexity_color = self.COLORS['yellow']
        
        print(f"{self.COLORS['white']}平均圈复杂度: {complexity_color}{avg_complexity:.2f}{self.COLORS['reset']}")
        
        # 复杂度解读
        if avg_complexity <= 10:
            print(f"  {self.COLORS['green']}✓ 复杂度良好{self.COLORS['reset']}")
        elif avg_complexity <= 20:
            print(f"  {self.COLORS['yellow']}⚠ 复杂度中等，建议重构{self.COLORS['reset']}")
        else:
            print(f"  {self.COLORS['red']}✗ 复杂度过高，需要立即重构{self.COLORS['reset']}")
    
    def _print_recommendations(self):
        """打印改进建议"""
        if not self.defects:
            return
        
        print(f"\n{self.COLORS['bold']}💡 改进建议{self.COLORS['reset']}")
        print("-"*40)
        
        recommendations = self._generate_recommendations()
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{self.COLORS['white']}{i}. {rec}{self.COLORS['reset']}")
    
    def _print_footer(self):
        """打印页脚"""
        print("\n" + "="*80)
        print(f"{self.COLORS['cyan']}分析完成！{self.COLORS['reset']}")
        print(f"{self.COLORS['cyan']}使用 '--format html' 选项生成更详细的HTML报告{self.COLORS['reset']}")
        print("="*80 + "\n")
    
    def _count_defects_by_severity(self) -> Dict[Severity, int]:
        """按严重程度统计缺陷"""
        counts = {}
        for defect in self.defects:
            sev = defect.severity
            counts[sev] = counts.get(sev, 0) + 1
        return counts
    
    def _calculate_quality_score(self) -> float:
        """计算质量分数"""
        if not self.defects:
            return 100.0
        
        # 基于缺陷数量和质量计算分数
        total_defects = len(self.defects)
        severity_counts = self._count_defects_by_severity()
        
        # 严重程度权重
        severity_weights = {
            Severity.CRITICAL: 10,
            Severity.HIGH: 5,
            Severity.MEDIUM: 2,
            Severity.LOW: 1,
        }
        
        # 计算加权缺陷分数
        weighted_score = sum(
            count * severity_weights.get(severity, 1)
            for severity, count in severity_counts.items()
        )
        
        # 基于代码量归一化
        total_lines = sum(m.get("total_lines", 0) for m in self.metrics)
        if total_lines == 0:
            total_lines = 1
        
        # 计算缺陷密度
        defect_density = weighted_score / total_lines * 1000
        
        # 转换为0-100的分数
        quality_score = 100 - min(defect_density * 10, 100)
        
        return max(0, quality_score)
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        severity_counts = self._count_defects_by_severity()
        
        # 严重缺陷建议
        if severity_counts.get(Severity.CRITICAL, 0) > 0:
            recommendations.append("立即修复所有严重缺陷（安全漏洞、硬编码密码等）")
        
        if severity_counts.get(Severity.HIGH, 0) > 0:
            recommendations.append("优先修复高危缺陷（空指针、资源泄漏、除以零等）")
        
        # 按缺陷模式建议
        pattern_counts = {}
        for defect in self.defects:
            pattern = defect.pattern
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        if "hardcoded_password" in pattern_counts:
            recommendations.append("移除硬编码的密码和密钥，使用环境变量")
        
        if "sql_injection" in pattern_counts:
            recommendations.append("修复SQL注入漏洞，使用参数化查询")
        
        if "null_dereference" in pattern_counts:
            recommendations.append("添加空值检查，使用Optional类型提示")
        
        if "resource_leak" in pattern_counts:
            recommendations.append("确保所有资源都正确关闭，使用with语句")
        
        # 基于指标的建议
        if self.metrics:
            complexities = [m.get("avg_cyclomatic_complexity", 0) 
                          for m in self.metrics if m.get("avg_cyclomatic_complexity", 0) > 0]
            avg_complexity = sum(complexities) / len(complexities) if complexities else 0
            
            if avg_complexity > 10:
                recommendations.append("重构高复杂度函数，降低圈复杂度")
        
        # 通用建议
        recommendations.append("添加单元测试覆盖关键代码路径")
        recommendations.append("定期运行代码分析，建立质量门禁")
        recommendations.append("使用类型注解提高代码可维护性")
        
        return recommendations[:5]  # 返回前5条建议
    
    def print_simple(self):
        """打印简化版报告"""
        total_defects = len(self.defects)
        
        if total_defects == 0:
            print(f"{self.COLORS['green']}✅ 未发现缺陷{self.COLORS['reset']}")
            return
        
        severity_counts = self._count_defects_by_severity()
        
        print(f"{self.COLORS['yellow']}⚠ 发现 {total_defects} 个缺陷:{self.COLORS['reset']}")
        
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                color = self.SEVERITY_COLORS.get(severity, self.COLORS['white'])
                severity_name = severity.value.upper()
                print(f"  {color}{severity_name}: {count}{self.COLORS['reset']}")