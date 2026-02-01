"""
测试用例集合
用于验证PyAnalyzer的检测能力
"""

# 测试1: 空指针解引用
def test_null_dereference():
    obj = None
    return obj.attribute  # 应该检测到

# 测试2: 资源泄漏
def test_resource_leak():
    f = open("test.txt", "r")  # 应该检测到
    data = f.read()
    # 忘记关闭文件
    return data

# 测试3: 除以零
def test_division_by_zero(x):
    return 100 / x  # 如果x为0，应该检测到

# 测试4: 硬编码密码
def test_hardcoded_password():
    password = "SuperSecret123!"  # 应该检测到
    api_key = "sk_live_1234567890abcdef"
    return password

# 测试5: SQL注入
def test_sql_injection(user_input):
    import sqlite3
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # 危险：字符串拼接
    query = f"SELECT * FROM users WHERE name = '{user_input}'"  # 应该检测到
    cursor.execute(query)
    
    return cursor.fetchall()

# 测试6: 不安全反序列化
def test_unsafe_deserialization(pickle_data):
    import pickle
    return pickle.loads(pickle_data)  # 应该检测到

# 测试7: 命令注入
def test_command_injection(filename):
    import os
    os.system(f"cat {filename}")  # 应该检测到
    return "done"

# 测试8: 无限循环
def test_infinite_loop():
    while True:  # 应该检测到
        print("Running...")

# 测试9: 复杂度过高的函数
def test_high_complexity(x):
    # 多层嵌套，复杂度高
    if x > 0:
        if x < 10:
            if x % 2 == 0:
                return "even small"
            else:
                return "odd small"
        elif x < 100:
            if x % 3 == 0:
                return "multiple of 3"
            elif x % 5 == 0:
                return "multiple of 5"
            else:
                return "other"
        else:
            if x < 1000:
                return "large"
            else:
                return "very large"
    elif x < 0:
        return "negative"
    else:
        return "zero"

# 测试10: 过长的函数
def test_long_function():
    step1()
    step2()
    step3()
    step4()
    step5()
    step6()
    step7()
    step8()
    step9()
    step10()
    step11()
    step12()
    step13()
    step14()
    step15()
    step16()
    step17()
    step18()
    step19()
    step20()
    step21()
    step22()
    step23()
    step24()
    step25()
    step26()
    step27()
    step28()
    step29()
    step30()
    return "done"

def step1(): pass
def step2(): pass
def step3(): pass
def step4(): pass
def step5(): pass
def step6(): pass
def step7(): pass
def step8(): pass
def step9(): pass
def step10(): pass
def step11(): pass
def step12(): pass
def step13(): pass
def step14(): pass
def step15(): pass
def step16(): pass
def step17(): pass
def step18(): pass
def step19(): pass
def step20(): pass
def step21(): pass
def step22(): pass
def step23(): pass
def step24(): pass
def step25(): pass
def step26(): pass
def step27(): pass
def step28(): pass
def step29(): pass
def step30(): pass

# 测试11: 未使用的变量
def test_unused_variables():
    x = 10  # 使用
    y = 20  # 未使用，应该检测到
    z = 30  # 未使用，应该检测到
    return x

# 测试12: 未使用的导入
import math  # 未使用，应该检测到
import os    # 使用
import sys   # 未使用，应该检测到

def test_unused_imports():
    os.getcwd()
    return "done"

# 测试13: 缺少类型注解
def test_missing_type_hints(param1, param2):  # 应该检测到
    return param1 + param2

# 测试14: 循环中字符串拼接
def test_string_concat_in_loop():
    result = ""
    for i in range(100):  # 应该检测到
        result += str(i)
    return result

# 测试15: 深度嵌套循环
def test_deep_nested_loops():
    for i in range(10):
        for j in range(10):
            for k in range(10):  # 三层嵌套，应该检测到
                for l in range(10):  # 四层嵌套，应该检测到
                    print(i, j, k, l)
    return "done"

# 测试16: 低效的成员测试
def test_inefficient_membership():
    my_list = [1, 2, 3, 4, 5]
    if 3 in my_list:  # 应该建议使用集合
        return "found"
    return "not found"

# 测试17: 不必要的拷贝
def test_unnecessary_copy():
    original = [1, 2, 3, 4, 5]
    for item in original[:]:  # 不必要的拷贝，应该检测到
        print(item)
    return "done"

# 测试18: 弱加密算法
def test_weak_cryptography():
    import hashlib
    # 使用弱哈希算法
    result = hashlib.md5(b"password")  # 应该检测到
    return result.hexdigest()

# 测试19: 不安全的随机数
def test_insecure_random():
    import random
    token = random.randint(1000, 9999)  # 用于安全场景，应该检测到
    return token

# 测试20: 路径遍历
def test_path_traversal(filename):
    import os
    with open(filename, 'r') as f:  # 如果filename包含..，应该检测到
        return f.read()

# 运行所有测试
if __name__ == "__main__":
    print("🔍 运行测试用例...")
    
    # 执行测试
    try:
        test_resource_leak()
        test_division_by_zero(1)
        test_hardcoded_password()
        test_sql_injection("test")
        test_infinite_loop()
        test_unused_variables()
        test_string_concat_in_loop()
        test_deep_nested_loops()
        test_inefficient_membership()
        test_unnecessary_copy()
        test_weak_cryptography()
        test_insecure_random()
        
        print("✅ 测试用例执行完成")
        print("⚠️  注意：这些函数包含故意设计的缺陷，用于测试PyAnalyzer的检测能力")
        
    except Exception as e:
        print(f"❌ 测试执行出错: {e}")