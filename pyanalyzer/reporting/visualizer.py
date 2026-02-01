"""
代码可视化模块
"""

import ast
import matplotlib.pyplot as plt
import networkx as nx
from typing import Dict, List, Any, Optional
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端


class CodeVisualizer:
    """代码可视化器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        with open(file_path, 'r', encoding='utf-8') as f:
            self.source_code = f.read()
        
        self.ast_tree = ast.parse(self.source_code)
        
        # 设置样式
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def generate_call_graph(self, output_path: str = None) -> str:
        """生成函数调用图"""
        if output_path is None:
            output_path = Path(self.file_path).stem + "_call_graph.png"
        
        # 构建调用图
        graph = nx.DiGraph()
        
        # 提取函数定义
        functions = []
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                graph.add_node(node.name, type='function', line=node.lineno)
        
        # 分析调用关系
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Call):
                # 获取调用者
                caller = self._get_enclosing_function(node)
                # 获取被调用者
                callee = self._extract_callee_name(node)
                
                if caller and callee and callee in functions:
                    graph.add_edge(caller, callee)
        
        # 绘制图形
        plt.figure(figsize=(12, 8))
        
        # 使用层次布局
        pos = nx.spring_layout(graph, k=2, iterations=50)
        
        # 节点颜色
        node_colors = []
        for node in graph.nodes():
            node_type = graph.nodes[node].get('type', 'function')
            if node_type == 'function':
                node_colors.append('lightblue')
            else:
                node_colors.append('lightgreen')
        
        # 绘制节点和边
        nx.draw_networkx_nodes(graph, pos, node_color=node_colors, 
                              node_size=800, alpha=0.8)
        nx.draw_networkx_edges(graph, pos, edge_color='gray', 
                              arrows=True, arrowsize=20, alpha=0.6)
        nx.draw_networkx_labels(graph, pos, font_size=10, font_weight='bold')
        
        plt.title(f"函数调用图 - {Path(self.file_path).name}", fontsize=16)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_ast_tree(self, output_path: str = None) -> str:
        """生成AST树图"""
        if output_path is None:
            output_path = Path(self.file_path).stem + "_ast_tree.png"
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(15, 10))
        
        # 递归绘制AST
        self._plot_ast_node(self.ast_tree, ax, x=0.5, y=0.95, width=1.0, depth=0)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        plt.title(f"抽象语法树 - {Path(self.file_path).name}", fontsize=16)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def _plot_ast_node(self, node: ast.AST, ax, x: float, y: float, 
                      width: float, depth: int):
        """递归绘制AST节点"""
        if depth > 5:  # 限制深度
            return
        
        # 获取节点类型
        node_type = type(node).__name__
        
        # 绘制节点
        ax.text(x, y, node_type, ha='center', va='center',
               bbox=dict(boxstyle="round,pad=0.3", 
                        facecolor="lightblue", 
                        edgecolor="black", 
                        alpha=0.8),
               fontsize=9)
        
        # 处理子节点
        children = list(ast.iter_child_nodes(node))
        num_children = len(children)
        
        if num_children > 0:
            # 计算子节点位置
            child_width = width / num_children
            child_x_start = x - width/2 + child_width/2
            
            for i, child in enumerate(children):
                child_x = child_x_start + i * child_width
                child_y = y - 0.1  # 垂直间距
                
                # 绘制连接线
                ax.plot([x, child_x], [y-0.02, child_y+0.02], 
                       'gray', linewidth=1, alpha=0.5)
                
                # 递归绘制子节点
                self._plot_ast_node(child, ax, child_x, child_y, 
                                   child_width * 0.9, depth + 1)
    
    def generate_complexity_chart(self, output_path: str = None) -> str:
        """生成复杂度图表"""
        if output_path is None:
            output_path = Path(self.file_path).stem + "_complexity.png"
        
        # 计算每个函数的圈复杂度
        complexities = []
        function_names = []
        
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                complexities.append(complexity)
                function_names.append(node.name)
        
        if not complexities:
            return None
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 柱状图
        bars = ax1.bar(range(len(complexities)), complexities, 
                      color=['red' if c > 10 else 'orange' if c > 5 else 'green' 
                            for c in complexities])
        ax1.set_xlabel('函数')
        ax1.set_ylabel('圈复杂度')
        ax1.set_title('函数圈复杂度分布')
        ax1.set_xticks(range(len(complexities)))
        ax1.set_xticklabels(function_names, rotation=45, ha='right')
        
        # 添加数值标签
        for i, (bar, complexity) in enumerate(zip(bars, complexities)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{complexity}', ha='center', va='bottom')
        
        # 饼图
        low = sum(1 for c in complexities if c <= 5)
        medium = sum(1 for c in complexities if 5 < c <= 10)
        high = sum(1 for c in complexities if c > 10)
        
        sizes = [low, medium, high]
        labels = ['低 (≤5)', '中 (6-10)', '高 (>10)']
        colors = ['green', 'orange', 'red']
        
        ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
               startangle=90)
        ax2.axis('equal')
        ax2.set_title('复杂度分布比例')
        
        plt.suptitle(f"代码复杂度分析 - {Path(self.file_path).name}", fontsize=16)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.Match):
                complexity += len(child.cases)
        
        return complexity
    
    def _get_enclosing_function(self, node: ast.AST) -> Optional[str]:
        """获取包含节点的函数名"""
        parent = node
        while hasattr(parent, 'parent'):
            parent = parent.parent
            if isinstance(parent, ast.FunctionDef):
                return parent.name
        return None
    
    def _extract_callee_name(self, node: ast.Call) -> Optional[str]:
        """提取被调用函数名"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None
    
    def generate_defect_distribution(self, defects: List[Dict], 
                                    output_path: str = None) -> str:
        """生成缺陷分布图"""
        if output_path is None:
            output_path = Path(self.file_path).stem + "_defects.png"
        
        # 按严重程度分组
        severity_counts = {}
        for defect in defects:
            severity = defect.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # 按模式分组
        pattern_counts = {}
        for defect in defects:
            pattern = defect.get('pattern', 'unknown')
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 严重程度饼图
        if severity_counts:
            labels = [k.upper() for k in severity_counts.keys()]
            sizes = list(severity_counts.values())
            colors = ['red', 'magenta', 'orange', 'yellow', 'green'][:len(sizes)]
            
            ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                   startangle=90)
            ax1.axis('equal')
            ax1.set_title('缺陷严重程度分布')
        
        # 缺陷模式柱状图
        if pattern_counts:
            patterns = list(pattern_counts.keys())
            counts = list(pattern_counts.values())
            
            # 排序
            sorted_indices = sorted(range(len(counts)), 
                                   key=lambda i: counts[i], reverse=True)
            patterns = [patterns[i] for i in sorted_indices]
            counts = [counts[i] for i in sorted_indices]
            
            bars = ax2.bar(range(len(counts)), counts)
            ax2.set_xlabel('缺陷模式')
            ax2.set_ylabel('数量')
            ax2.set_title('缺陷模式分布')
            ax2.set_xticks(range(len(patterns)))
            ax2.set_xticklabels(patterns, rotation=45, ha='right')
            
            # 添加数值标签
            for i, (bar, count) in enumerate(zip(bars, counts)):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{count}', ha='center', va='bottom')
        
        plt.suptitle(f"缺陷分布分析 - {Path(self.file_path).name}", fontsize=16)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_combined_report(self, defects: List[Dict], 
                                metrics: Dict, output_dir: str = None) -> Dict:
        """生成综合可视化报告"""
        if output_dir is None:
            output_dir = Path(self.file_path).parent / "visualizations"
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        report_files = {}
        
        # 生成所有图表
        try:
            report_files['call_graph'] = self.generate_call_graph(
                str(Path(output_dir) / "call_graph.png")
            )
        except Exception as e:
            print(f"生成调用图失败: {e}")
        
        try:
            report_files['ast_tree'] = self.generate_ast_tree(
                str(Path(output_dir) / "ast_tree.png")
            )
        except Exception as e:
            print(f"生成AST树失败: {e}")
        
        try:
            report_files['complexity'] = self.generate_complexity_chart(
                str(Path(output_dir) / "complexity.png")
            )
        except Exception as e:
            print(f"生成复杂度图表失败: {e}")
        
        if defects:
            try:
                report_files['defects'] = self.generate_defect_distribution(
                    defects, str(Path(output_dir) / "defects.png")
                )
            except Exception as e:
                print(f"生成缺陷分布图失败: {e}")
        
        # 生成HTML摘要
        html_path = self._generate_html_summary(report_files, metrics, 
                                               str(Path(output_dir) / "summary.html"))
        report_files['summary'] = html_path
        
        return report_files
    
    def _generate_html_summary(self, report_files: Dict, 
                              metrics: Dict, output_path: str) -> str:
        """生成HTML摘要"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>代码分析可视化摘要 - {Path(self.file_path).name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                h1 {{ color: #333; }}
                .section {{ margin-bottom: 30px; }}
                .image-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
                .image-card {{ border: 1px solid #ddd; padding: 10px; text-align: center; }}
                .image-card img {{ max-width: 100%; height: auto; }}
                .metrics {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .metric-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 代码分析可视化摘要</h1>
                <p><strong>文件:</strong> {self.file_path}</p>
                <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="section">
                    <h2>📈 代码指标</h2>
                    <div class="metrics">
                        {self._generate_metrics_html(metrics)}
                    </div>
                </div>
                
                <div class="section">
                    <h2>🖼️ 可视化图表</h2>
                    <div class="image-grid">
                        {self._generate_images_html(report_files)}
                    </div>
                </div>
                
                <div class="section">
                    <h2>📋 文件列表</h2>
                    <ul>
                        {self._generate_file_list_html(report_files)}
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_metrics_html(self, metrics: Dict) -> str:
        """生成指标HTML"""
        if not metrics:
            return "<p>暂无指标数据</p>"
        
        html = ""
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                html += f"""
                <div class="metric-row">
                    <span>{key}:</span>
                    <span><strong>{value:.2f if isinstance(value, float) else value}</strong></span>
                </div>
                """
        
        return html
    
    def _generate_images_html(self, report_files: Dict) -> str:
        """生成图片HTML"""
        html = ""
        
        for name, path in report_files.items():
            if path and path.endswith('.png'):
                img_name = Path(path).name
                html += f"""
                <div class="image-card">
                    <h3>{name.replace('_', ' ').title()}</h3>
                    <img src="{img_name}" alt="{name}">
                    <p>{img_name}</p>
                </div>
                """
        
        return html
    
    def _generate_file_list_html(self, report_files: Dict) -> str:
        """生成文件列表HTML"""
        html = ""
        
        for name, path in report_files.items():
            if path:
                html += f'<li><a href="{Path(path).name}">{name}: {Path(path).name}</a></li>'
        
        return html