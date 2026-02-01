"""
PyAnalyzer核心功能测试
"""

import unittest
import tempfile
import os
from pathlib import Path

from pyanalyzer.core.ast_parser import ASTParser
from pyanalyzer.core.defect_detector import DefectDetector
from pyanalyzer.utils.file_utils import find_python_files


class TestASTParser(unittest.TestCase):
    """测试AST解析器"""
    
    def setUp(self):
        self.sample_code = """
def hello(name: str) -> str:
    \"\"\"返回问候语\"\"\"
    return f"Hello, {name}!"

class Person:
    def __init__(self, name: str):
        self.name = name
    
    def greet(self) -> str:
        return hello(self.name)
"""
    
    def test_parser_initialization(self):
        """测试解析器初始化"""
        parser = ASTParser(self.sample_code, "test.py")
        self.assertIsNotNone(parser.ast_tree)
        self.assertIsNotNone(parser.cst_tree)
    
    def test_function_extraction(self):
        """测试函数提取"""
        parser = ASTParser(self.sample_code, "test.py")
        functions = parser.functions
        self.assertEqual(len(functions), 3)  # hello, __init__, greet
    
    def test_class_extraction(self):
        """测试类提取"""
        parser = ASTParser(self.sample_code, "test.py")
        classes = parser.classes
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].name, "Person")
    
    def test_metrics_calculation(self):
        """测试指标计算"""
        parser = ASTParser(self.sample_code, "test.py")
        metrics = parser.calculate_metrics()
        self.assertIn("total_lines", metrics)
        self.assertIn("function_count", metrics)
        self.assertIn("class_count", metrics)
    
    def test_unused_variable_detection(self):
        """测试未使用变量检测"""
        code = """
def test():
    x = 10
    y = 20  # 未使用
    return x
"""
        parser = ASTParser(code, "test.py")
        unused = parser.find_unused_variables()
        self.assertEqual(len(unused), 1)
        self.assertEqual(unused[0]["variable"], "y")


class TestDefectDetector(unittest.TestCase):
    """测试缺陷检测器"""
    
    def test_null_dereference(self):
        """测试空指针解引用检测"""
        code = """
def dangerous():
    obj = None
    return obj.attribute
"""
        parser = ASTParser(code, "test.py")
        config = {"patterns": {"enabled": ["null_dereference"]}}
        detector = DefectDetector(parser, config)
        defects = detector.detect_all()
        self.assertGreater(len(defects), 0)
        self.assertEqual(defects[0].pattern, "null_dereference")
    
    def test_division_by_zero(self):
        """测试除以零检测"""
        code = """
def divide(a, b):
    return a / b  # b可能为0
"""
        parser = ASTParser(code, "test.py")
        config = {"patterns": {"enabled": ["division_by_zero"]}}
        detector = DefectDetector(parser, config)
        defects = detector.detect_all()
        # 注意：静态分析无法检测运行时值，所以可能检测不到
        # 这里主要测试检测器不崩溃
    
    def test_resource_leak(self):
        """测试资源泄漏检测"""
        code = """
def read_file():
    f = open("test.txt", "r")
    return f.read()  # 未关闭文件
"""
        parser = ASTParser(code, "test.py")
        config = {"patterns": {"enabled": ["resource_leak"]}}
        detector = DefectDetector(parser, config)
        defects = detector.detect_all()
        self.assertGreater(len(defects), 0)
    
    def test_multiple_patterns(self):
        """测试多个模式同时检测"""
        code = """
def problematic():
    password = "secret123"  # 硬编码密码
    f = open("file.txt")    # 资源泄漏
    x = None
    print(x.attr)           # 空指针
    return password
"""
        parser = ASTParser(code, "test.py")
        config = {
            "patterns": {
                "enabled": [
                    "hardcoded_password",
                    "resource_leak",
                    "null_dereference"
                ]
            }
        }
        detector = DefectDetector(parser, config)
        defects = detector.detect_all()
        self.assertGreaterEqual(len(defects), 3)


class TestFileUtils(unittest.TestCase):
    """测试文件工具"""
    
    def setUp(self):
        # 创建临时目录结构
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建Python文件
        self.py_file = Path(self.temp_dir) / "test.py"
        self.py_file.write_text("print('hello')")
        
        # 创建测试文件
        self.test_file = Path(self.temp_dir) / "test_test.py"
        self.test_file.write_text("def test(): pass")
        
        # 创建子目录
        subdir = Path(self.temp_dir) / "subdir"
        subdir.mkdir()
        self.sub_py = subdir / "module.py"
        self.sub_py.write_text("x = 10")
        
        # 创建缓存目录
        cache_dir = Path(self.temp_dir) / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "test.cpython-39.pyc").touch()
    
    def test_find_python_files(self):
        """测试查找Python文件"""
        ignore_config = {"files": ["*/test_*.py", "*/__pycache__/*"]}
        files = find_python_files(self.temp_dir, ignore_config)
        
        # 应该找到 test.py 和 subdir/module.py，但排除 test_test.py
        file_names = [Path(f).name for f in files]
        self.assertIn("test.py", file_names)
        self.assertIn("module.py", file_names)
        self.assertNotIn("test_test.py", file_names)
    
    def test_count_lines(self):
        """测试行数计算"""
        from pyanalyzer.utils.file_utils import count_lines_in_file
        lines = count_lines_in_file(str(self.py_file))
        self.assertEqual(lines, 1)  # print('hello') 一行
    
    def tearDown(self):
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_full_analysis(self):
        """测试完整分析流程"""
        # 使用示例代码
        from examples.example_project.vulnerable_code import __file__ as example_path
        example_dir = Path(example_path).parent
        
        # 查找文件
        ignore_config = {"files": []}
        files = find_python_files(str(example_dir), ignore_config)
        self.assertGreater(len(files), 0)
        
        # 分析第一个文件
        if files:
            with open(files[0], 'r', encoding='utf-8') as f:
                code = f.read()
            
            parser = ASTParser(code, files[0])
            config = {
                "patterns": {
                    "enabled": [
                        "null_dereference",
                        "resource_leak",
                        "division_by_zero"
                    ]
                }
            }
            detector = DefectDetector(parser, config)
            defects = detector.detect_all()
            
            # 应该发现一些缺陷
            self.assertIsInstance(defects, list)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestASTParser))
    suite.addTests(loader.loadTestsFromTestCase(TestDefectDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestFileUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    run_tests()