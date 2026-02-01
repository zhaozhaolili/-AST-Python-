"""
HTML报告生成器
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from pyanalyzer.patterns.base_patterns import Defect, Severity


class HTMLReporter:
    """HTML报告生成器"""
    
    def __init__(self, defects: List[Defect], metrics: List[Dict], config: Dict):
        self.defects = defects
        self.metrics = metrics
        self.config = config
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def generate(self, output_dir: str) -> str:
        """生成HTML报告"""
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成报告内容
        html_content = self._generate_html()
        
        # 写入文件
        output_path = Path(output_dir) / "analysis_report.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 生成JSON数据供JavaScript使用
        self._generate_json_data(output_dir)
        
        return str(output_path)
    
    def _generate_html(self) -> str:
        """生成完整的HTML页面"""
        severity_counts = self._count_defects_by_severity()
        pattern_counts = self._count_defects_by_pattern()
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyAnalyzer - Python代码分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        
        .subtitle {{
            color: #7f8c8d;
            font-size: 1.1em;
        }}
        
        .timestamp {{
            background: #3498db;
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 10px;
            font-weight: bold;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .card h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f8f9fa;
            font-size: 1.4em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            background: #f8f9fa;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        
        .severity-critical {{ color: #e74c3c; }}
        .severity-high {{ color: #e67e22; }}
        .severity-medium {{ color: #f1c40f; }}
        .severity-low {{ color: #3498db; }}
        
        .defects-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .defects-table th {{
            background: #2c3e50;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        .defects-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        
        .defects-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .severity-badge {{
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .badge-critical {{ background: #e74c3c; color: white; }}
        .badge-high {{ background: #e67e22; color: white; }}
        .badge-medium {{ background: #f1c40f; color: white; }}
        .badge-low {{ background: #3498db; color: white; }}
        
        .chart-container {{
            position: relative;
            height: 300px;
            margin-top: 20px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .metric-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        
        .metric-name {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .metric-value {{
            font-size: 1.5em;
            color: #3498db;
        }}
        
        .summary {{
            margin-top: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #1abc9c, #16a085);
            color: white;
            border-radius: 10px;
            text-align: center;
        }}
        
        .summary h2 {{
            margin-bottom: 15px;
            font-size: 1.8em;
        }}
        
        .recommendations {{
            margin-top: 30px;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .recommendations ul {{
            padding-left: 20px;
        }}
        
        .recommendations li {{
            margin-bottom: 10px;
            padding-left: 10px;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: white;
            margin-top: 30px;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .dashboard {{
                grid-template-columns: 1fr;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .defects-table {{
                display: block;
                overflow-x: auto;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 PyAnalyzer 代码分析报告</h1>
            <p class="subtitle">基于AST与符号执行的Python代码缺陷检测</p>
            <div class="timestamp">生成时间: {self.timestamp}</div>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h2>📊 总体统计</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value severity-critical">{severity_counts.get('critical', 0)}</div>
                        <div class="stat-label">严重缺陷</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value severity-high">{severity_counts.get('high', 0)}</div>
                        <div class="stat-label">高危缺陷</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value severity-medium">{severity_counts.get('medium', 0)}</div>
                        <div class="stat-label">中危缺陷</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value severity-low">{severity_counts.get('low', 0)}</div>
                        <div class="stat-label">低危缺陷</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>📈 缺陷分布</h2>
                <div class="chart-container">
                    <canvas id="defectsChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h2>⚙️ 分析配置</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-name">分析文件数</div>
                        <div class="metric-value">{len(self.metrics)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-name">启用模式数</div>
                        <div class="metric-value">{len(self.config.get('patterns', {}).get('enabled', []))}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-name">符号执行</div>
                        <div class="metric-value">{"启用" if self.config.get('symbolic_execution', {}).get('enabled', False) else "禁用"}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>🔎 缺陷详情</h2>
            {self._generate_defects_table()}
        </div>
        
        {self._generate_metrics_section()}
        
        <div class="summary">
            <h2>📋 分析总结</h2>
            <p>本次分析共发现 {len(self.defects)} 个代码缺陷，其中严重和高危缺陷 {severity_counts.get('critical', 0) + severity_counts.get('high', 0)} 个。</p>
            <p>建议优先修复严重和高危缺陷，以提高代码质量和安全性。</p>
        </div>
        
        <div class="recommendations">
            <h2>💡 改进建议</h2>
            <ul>
                {self._generate_recommendations()}
            </ul>
        </div>
        
        <div class="footer">
            <p>Generated by PyAnalyzer | 基于Python AST与Z3符号执行 | 仅供学习使用</p>
        </div>
    </div>
    
    <script>
        // 图表数据
        const patternData = {json.dumps(pattern_counts)};
        
        // 准备图表数据
        const labels = Object.keys(patternData);
        const data = Object.values(patternData);
        const colors = [
            '#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', 
            '#3498db', '#9b59b6', '#1abc9c', '#34495e'
        ];
        
        // 缺陷分布图表
        const defectsChart = new Chart(
            document.getElementById('defectsChart'),
            {{
                type: 'doughnut',
                data: {{
                    labels: labels,
                    datasets: [{{
                        data: data,
                        backgroundColor: colors,
                        borderWidth: 1,
                        borderColor: '#fff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'right',
                            labels: {{
                                padding: 20,
                                font: {{
                                    size: 12
                                }}
                            }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const label = context.label || '';
                                    const value = context.raw || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = Math.round((value / total) * 100);
                                    return `${{label}}: ${{value}} (${{percentage}}%)`;
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        );
        
        // 点击缺陷行显示详情
        document.querySelectorAll('.defect-row').forEach(row => {{
            row.addEventListener('click', function() {{
                const defectId = this.dataset.defectId;
                const modal = document.getElementById(`defect-modal-${{defectId}}`);
                if (modal) {{
                    modal.style.display = 'block';
                }}
            }});
        }});
        
        // 关闭模态框
        document.querySelectorAll('.close-modal').forEach(btn => {{
            btn.addEventListener('click', function() {{
                this.closest('.modal').style.display = 'none';
            }});
        }});
    </script>
</body>
</html>
"""
        
        return html
    
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
    
    def _generate_defects_table(self) -> str:
        """生成缺陷表格"""
        if not self.defects:
            return '<p style="text-align: center; padding: 20px; color: #27ae60;">🎉 未发现缺陷！</p>'
        
        rows = []
        for i, defect in enumerate(self.defects):
            severity_class = f"badge-{defect.severity.value}"
            rows.append(f"""
                <tr class="defect-row" data-defect-id="{i}">
                    <td><span class="severity-badge {severity_class}">{defect.severity.value.upper()}</span></td>
                    <td><strong>{defect.pattern}</strong></td>
                    <td>{defect.description}</td>
                    <td>{Path(defect.file_path).name}:{defect.line}</td>
                    <td>{defect.suggestion or '无'}</td>
                </tr>
            """)
        
        table = f"""
        <table class="defects-table">
            <thead>
                <tr>
                    <th>严重程度</th>
                    <th>模式</th>
                    <th>描述</th>
                    <th>位置</th>
                    <th>建议</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
        
        return table
    
    def _generate_metrics_section(self) -> str:
        """生成指标部分"""
        if not self.metrics:
            return ""
        
        # 计算总体指标
        total_lines = sum(m.get('total_lines', 0) for m in self.metrics)
        total_functions = sum(m.get('function_count', 0) for m in self.metrics)
        total_classes = sum(m.get('class_count', 0) for m in self.metrics)
        
        avg_complexity = 0
        complexities = [m.get('avg_cyclomatic_complexity', 0) for m in self.metrics if m.get('avg_cyclomatic_complexity', 0) > 0]
        if complexities:
            avg_complexity = sum(complexities) / len(complexities)
        
        return f"""
        <div class="card">
            <h2>📏 代码指标</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-name">总代码行数</div>
                    <div class="metric-value">{total_lines}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-name">函数数量</div>
                    <div class="metric-value">{total_functions}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-name">类数量</div>
                    <div class="metric-value">{total_classes}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-name">平均圈复杂度</div>
                    <div class="metric-value">{avg_complexity:.2f}</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_recommendations(self) -> str:
        """生成改进建议"""
        recommendations = []
        
        severity_counts = self._count_defects_by_severity()
        
        if severity_counts.get('critical', 0) > 0:
            recommendations.append("<li>立即修复所有<strong>严重</strong>缺陷，特别是SQL注入和硬编码密码问题</li>")
        
        if severity_counts.get('high', 0) > 0:
            recommendations.append("<li>优先处理<strong>高危</strong>缺陷，如空指针解引用和除以零</li>")
        
        if any('unused' in pattern for pattern in self._count_defects_by_pattern().keys()):
            recommendations.append("<li>清理未使用的变量和导入，提高代码可读性</li>")
        
        if any('missing_type_hints' == pattern for pattern in self._count_defects_by_pattern().keys()):
            recommendations.append("<li>为关键函数添加类型注解，提高代码可维护性</li>")
        
        if any('long_function' == pattern for pattern in self._count_defects_by_pattern().keys()):
            recommendations.append("<li>重构过长的函数，遵循单一职责原则</li>")
        
        recommendations.append("<li>定期运行代码分析，建立代码质量检查流程</li>")
        recommendations.append("<li>考虑使用CI/CD集成代码分析工具</li>")
        
        return '\n'.join(recommendations)
    
    def _generate_json_data(self, output_dir: str):
        """生成JSON数据文件"""
        data = {
            "timestamp": self.timestamp,
            "total_defects": len(self.defects),
            "defects_by_severity": self._count_defects_by_severity(),
            "defects_by_pattern": self._count_defects_by_pattern(),
            "defects": [
                {
                    "pattern": d.pattern,
                    "description": d.description,
                    "severity": d.severity.value,
                    "line": d.line,
                    "file": d.file_path,
                    "suggestion": d.suggestion
                }
                for d in self.defects
            ],
            "metrics": self.metrics,
            "config": self.config
        }
        
        json_path = Path(output_dir) / "analysis_data.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)