"""
调用图分析模块
"""

import ast
import networkx as nx
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class CallGraphAnalyzer:
    """调用图分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.graph = nx.DiGraph()
        self.function_calls = defaultdict(set)
        self.class_hierarchy = defaultdict(set)
        
    def build_call_graph(self):
        """构建调用图"""
        # 添加所有函数作为节点
        for func in self.parser.functions:
            self.graph.add_node(
                func.name,
                type='function',
                line=func.lineno,
                complexity=func.complexity
            )
        
        # 添加所有类作为节点
        for cls in self.parser.classes:
            self.graph.add_node(
                cls.name,
                type='class',
                line=cls.lineno
            )
            
            # 添加类方法
            for method in cls.methods:
                self.graph.add_node(
                    f"{cls.name}.{method.name}",
                    type='method',
                    line=method.lineno,
                    complexity=method.complexity
                )
        
        # 分析调用关系
        self._analyze_calls()
        
        # 添加调用边
        for caller, callees in self.function_calls.items():
            for callee in callees:
                if callee in self.graph:
                    self.graph.add_edge(caller, callee)
        
        return self.graph
    
    def _analyze_calls(self):
        """分析函数调用关系"""
        # 遍历AST，收集调用信息
        for node in ast.walk(self.parser.ast_tree):
            if isinstance(node, ast.Call):
                caller = self._get_enclosing_function(node)
                callee = self._extract_callee_name(node)
                
                if caller and callee:
                    self.function_calls[caller].add(callee)
    
    def _get_enclosing_function(self, node: ast.AST) -> str:
        """获取包含给定节点的函数名"""
        parent = node
        while hasattr(parent, 'parent'):
            parent = parent.parent
            if isinstance(parent, ast.FunctionDef):
                # 检查是否是类方法
                class_parent = parent
                while hasattr(class_parent, 'parent'):
                    class_parent = class_parent.parent
                    if isinstance(class_parent, ast.ClassDef):
                        return f"{class_parent.name}.{parent.name}"
                return parent.name
        return None
    
    def _extract_callee_name(self, node: ast.Call) -> str:
        """提取被调用函数名"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            # 处理obj.method()形式的调用
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
        return None
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """查找循环依赖"""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except nx.NetworkXNoCycle:
            return []
    
    def calculate_coupling_metrics(self) -> Dict:
        """计算耦合度指标"""
        if not self.graph.nodes:
            return {}
        
        # 计算传入耦合（afferent coupling）
        afferent = {}
        for node in self.graph.nodes():
            predecessors = list(self.graph.predecessors(node))
            afferent[node] = len(predecessors)
        
        # 计算传出耦合（efferent coupling）
        efferent = {}
        for node in self.graph.nodes():
            successors = list(self.graph.successors(node))
            efferent[node] = len(successors)
        
        # 计算不稳定性
        instability = {}
        for node in self.graph.nodes():
            ce = efferent.get(node, 0)
            ca = afferent.get(node, 0)
            if ce + ca > 0:
                instability[node] = ce / (ce + ca)
            else:
                instability[node] = 0
        
        return {
            'afferent_coupling': afferent,
            'efferent_coupling': efferent,
            'instability': instability,
            'total_nodes': len(self.graph.nodes()),
            'total_edges': len(self.graph.edges()),
        }
    
    def find_most_coupled_functions(self, n: int = 10) -> List[Tuple[str, int]]:
        """找出耦合度最高的函数"""
        coupling = {}
        for node in self.graph.nodes():
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)
            coupling[node] = in_degree + out_degree
        
        sorted_coupling = sorted(coupling.items(), key=lambda x: x[1], reverse=True)
        return sorted_coupling[:n]
    
    def visualize(self, output_path: str = "call_graph.png"):
        """可视化调用图"""
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(12, 8))
        
        # 使用层次布局
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        # 根据节点类型设置颜色
        node_colors = []
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('type', 'function')
            if node_type == 'function':
                node_colors.append('lightblue')
            elif node_type == 'class':
                node_colors.append('lightgreen')
            elif node_type == 'method':
                node_colors.append('lightcoral')
            else:
                node_colors.append('gray')
        
        nx.draw(
            self.graph,
            pos,
            with_labels=True,
            node_color=node_colors,
            node_size=800,
            font_size=10,
            font_weight='bold',
            edge_color='gray',
            alpha=0.8
        )
        
        plt.title("函数调用图", fontsize=16)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def export_to_dot(self, output_path: str = "call_graph.dot"):
        """导出为DOT格式"""
        nx.drawing.nx_pydot.write_dot(self.graph, output_path)
        return output_path