"""
JSON报告生成器
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from pyanalyzer.patterns.base_patterns import Defect


class JSONReporter:
    """JSON报告生成器"""
    
    def __init__(self, defects: List[Defect], metrics: List[Dict], config: Dict):
        self.defects = defects
        self.metrics = metrics
        self.config = config
        self.timestamp = datetime.now().isoformat()
        
    def generate(self, output_dir: str) -> str:
        """生成JSON报告"""
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成报告数据
        report_data = self._generate_report_data()
        
        # 写入文件
        output_path = Path(output_dir) / "analysis_report.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # 生成摘要文件
        summary_path = Path(output_dir) / "summary.json"
        summary_data = self._generate_summary_data(report_data)
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def _generate_report_data(self) -> Dict[str, Any]:
        """生成完整的报告数据"""
        # 按文件分组缺陷
        defects_by_file = {}
        for defect in self.defects:
            file_path = defect.file_path
            if file_path not in defects_by_file:
                defects_by_file[file_path] = []
            
            defects_by_file[file_path].append({
                "pattern": defect.pattern,
                "description": defect.description,
                "severity": defect.severity.value,
                "line": defect.line,
                "context": defect.context,
                "suggestion": defect.suggestion
            })
        
        # 统计信息
        severity_counts = self._count_defects_by_severity()
        pattern_counts = self._count_defects_by_pattern()
        
        # 项目指标
        project_metrics = self._calculate_project_metrics()
        
        # 生成报告
        report_data = {
            "metadata": {
                "tool": "PyAnalyzer",
                "version": "1.0.0",
                "timestamp": self.timestamp,
                "config": self.config
            },
            "summary": {
                "total_defects": len(self.defects),
                "severity_distribution": severity_counts,
                "pattern_distribution": pattern_counts,
                "files_analyzed": len(self.metrics),
                "project_metrics": project_metrics
            },
            "defects": {
                "by_file": defects_by_file,
                "all": [
                    {
                        "id": i,
                        "pattern": d.pattern,
                        "description": d.description,
                        "severity": d.severity.value,
                        "file": d.file_path,
                        "line": d.line,
                        "suggestion": d.suggestion
                    }
                    for i, d in enumerate(self.defects)
                ]
            },
            "metrics": {
                "files": self.metrics,
                "aggregated": project_metrics
            },
            "analysis": {
                "config_used": self.config,
                "patterns_enabled": self.config.get("patterns", {}).get("enabled", []),
                "symbolic_execution_enabled": self.config.get("symbolic_execution", {}).get("enabled", False)
            }
        }
        
        return report_data
    
    def _generate_summary_data(self, report_data: Dict) -> Dict[str, Any]:
        """生成摘要数据"""
        summary = {
            "timestamp": self.timestamp,
            "total_defects": report_data["summary"]["total_defects"],
            "severity_summary": report_data["summary"]["severity_distribution"],
            "top_patterns": dict(sorted(
                report_data["summary"]["pattern_distribution"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            "files_with_defects": len(report_data["defects"]["by_file"]),
            "total_files_analyzed": report_data["summary"]["files_analyzed"],
            "key_metrics": {
                "total_lines": report_data["summary"]["project_metrics"].get("total_lines", 0),
                "total_functions": report_data["summary"]["project_metrics"].get("total_functions", 0),
                "avg_complexity": report_data["summary"]["project_metrics"].get("avg_complexity", 0)
            }
        }
        
        # 添加建议
        summary["recommendations"] = self._generate_recommendations(report_data)
        
        return summary
    
    def _count_defects_by_severity(self) -> Dict[str, int]:
        """按严重程度统计缺陷"""
        counts = {}
        for defect in self.defects:
            sev = defect.severity.value
            counts[sev] = counts.get(sev, 0) + 1
        return counts
    
    def _count_defects_by_pattern(self) -> Dict[str, int]:
        """按模式统计缺陷"""
        counts = {}
        for defect in self.defects:
            pattern = defect.pattern
            counts[pattern] = counts.get(pattern, 0) + 1
        return counts
    
    def _calculate_project_metrics(self) -> Dict[str, Any]:
        """计算项目级指标"""
        if not self.metrics:
            return {}
        
        total_lines = sum(m.get("total_lines", 0) for m in self.metrics)
        total_functions = sum(m.get("function_count", 0) for m in self.metrics)
        total_classes = sum(m.get("class_count", 0) for m in self.metrics)
        
        # 计算平均复杂度
        complexities = [m.get("avg_cyclomatic_complexity", 0) 
                       for m in self.metrics if m.get("avg_cyclomatic_complexity", 0) > 0]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        
        # 计算平均函数长度
        func_lengths = [m.get("avg_function_length", 0) 
                       for m in self.metrics if m.get("avg_function_length", 0) > 0]
        avg_function_length = sum(func_lengths) / len(func_lengths) if func_lengths else 0
        
        return {
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "avg_cyclomatic_complexity": avg_complexity,
            "avg_function_length": avg_function_length,
            "files_analyzed": len(self.metrics)
        }
    
    def _generate_recommendations(self, report_data: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        severity_counts = report_data["summary"]["severity_distribution"]
        
        # 根据缺陷严重程度生成建议
        if severity_counts.get("critical", 0) > 0:
            recommendations.append("立即修复所有严重缺陷，特别是安全相关的问题")
        
        if severity_counts.get("high", 0) > 0:
            recommendations.append("优先处理高危缺陷，确保代码稳定性和安全性")
        
        # 根据缺陷模式生成建议
        pattern_counts = report_data["summary"]["pattern_distribution"]
        
        if "hardcoded_password" in pattern_counts:
            recommendations.append("移除所有硬编码的密码和密钥，使用环境变量或密钥管理服务")
        
        if "sql_injection" in pattern_counts:
            recommendations.append("将所有SQL查询改为参数化查询，使用ORM框架")
        
        if "null_dereference" in pattern_counts:
            recommendations.append("添加空值检查，使用Optional类型注解")
        
        if "resource_leak" in pattern_counts:
            recommendations.append("确保所有资源（文件、连接）都使用with语句或正确关闭")
        
        # 根据指标生成建议
        metrics = report_data["summary"]["project_metrics"]
        if metrics.get("avg_complexity", 0) > 10:
            recommendations.append("重构高复杂度函数，降低圈复杂度")
        
        if metrics.get("avg_function_length", 0) > 30:
            recommendations.append("拆分过长的函数，遵循单一职责原则")
        
        return recommendations
    
    def generate_statistics(self) -> Dict[str, Any]:
        """生成统计数据"""
        report_data = self._generate_report_data()
        
        stats = {
            "defect_density": 0,
            "quality_score": 100,
            "risk_level": "low"
        }
        
        # 计算缺陷密度（每千行代码的缺陷数）
        total_lines = report_data["summary"]["project_metrics"].get("total_lines", 1)
        total_defects = report_data["summary"]["total_defects"]
        
        if total_lines > 0:
            stats["defect_density"] = (total_defects / total_lines) * 1000
        
        # 计算质量分数（基于缺陷严重程度）
        severity_weights = {
            "critical": 10,
            "high": 5,
            "medium": 2,
            "low": 1
        }
        
        severity_scores = sum(
            count * severity_weights.get(severity, 1)
            for severity, count in report_data["summary"]["severity_distribution"].items()
        )
        
        # 基于代码量和缺陷严重程度计算质量分数
        if total_lines > 0:
            base_score = 100
            penalty = min(severity_scores * 100 / total_lines, 100)
            stats["quality_score"] = max(0, base_score - penalty)
        
        # 确定风险等级
        if severity_scores > 50 or stats["defect_density"] > 10:
            stats["risk_level"] = "high"
        elif severity_scores > 20 or stats["defect_density"] > 5:
            stats["risk_level"] = "medium"
        
        return stats