"""
包含各种缺陷模式的示例代码
用于测试PyAnalyzer
"""

import os
import sqlite3
from typing import Optional


def divide_numbers(a: int, b: int) -> float:
    """
    除法函数 - 可能除以零
    """
    result = a / b  # 缺陷：可能除以零
    return result


def process_file(filename: str):
    """
    处理文件 - 可能资源泄漏
    """
    f = open(filename, 'r')  # 缺陷：未使用with语句
    content = f.read()
    # 忘记关闭文件
    return content


def get_user_password(user_id: int) -> str:
    """
    获取用户密码 - 硬编码密码
    """
    password = "admin123"  # 缺陷：硬编码密码
    api_key = "sk_live_1234567890abcdef"  # 缺陷：硬编码密钥
    return password


def query_database(user_input: str):
    """
    查询数据库 - SQL注入漏洞
    """
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 危险：字符串拼接
    query = f"SELECT * FROM users WHERE name = '{user_input}'"  # 缺陷：SQL注入
    cursor.execute(query)
    
    # 稍好的方式，但仍然有问题
    query2 = "SELECT * FROM users WHERE name = %s" % user_input  # 缺陷：SQL注入
    cursor.execute(query2)
    
    return cursor.fetchall()


def access_none_object():
    """
    访问None对象 - 空指针解引用
    """
    obj = None
    return obj.attribute  # 缺陷：访问None的属性


def infinite_loop():
    """
    无限循环 - 可能永不终止
    """
    while True:  # 缺陷：无限循环
        print("Running...")
        # 缺少退出条件


def unused_variables():
    """
    未使用的变量
    """
    x = 10
    y = 20  # 定义了但未使用
    z = 30  # 定义了但未使用
    return x


def missing_type_hints(param1, param2):
    """
    缺少类型注解
    """
    # 缺少参数和返回类型注解
    return param1 + param2


def long_function():
    """
    过长的函数
    """
    # 模拟一个很长的函数
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


class ComplexClass:
    """
    复杂的类 - 高圈复杂度
    """
    
    def complex_method(self, value: int) -> str:
        if value > 0:
            if value < 10:
                if value % 2 == 0:
                    return "even small positive"
                else:
                    return "odd small positive"
            elif value < 100:
                if value % 3 == 0:
                    return "multiple of 3"
                elif value % 5 == 0:
                    return "multiple of 5"
                else:
                    return "other"
            else:
                return "large"
        elif value < 0:
            return "negative"
        else:
            return "zero"


def use_assert():
    """
    使用assert - 生产环境中可能被禁用
    """
    x = 10
    assert x > 0, "x must be positive"  # 缺陷：assert在生产中可能被禁用
    return x


def main():
    """主函数"""
    # 测试各种函数
    try:
        result = divide_numbers(10, 0)
        print(f"除法结果: {result}")
    except ZeroDivisionError:
        print("除以零错误")
    
    # 测试数据库查询
    user_input = input("请输入用户名: ")
    query_database(user_input)
    
    # 测试文件处理
    process_file("test.txt")
    
    # 测试None访问
    try:
        access_none_object()
    except AttributeError:
        print("None对象访问错误")
    
    print("程序结束")


if __name__ == "__main__":
    main()