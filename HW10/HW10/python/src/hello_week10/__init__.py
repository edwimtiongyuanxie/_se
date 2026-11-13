"""
HW10 Python Package Example
"""

__version__ = "0.1.0"


def hello(name: str = "World") -> str:
    """回傳一句問候語"""
    return f"Hello, {name}! This is HW10 Python package."


def add(a: int, b: int) -> int:
    """簡單加法"""
    return a + b


def greet_student(student_id: str) -> str:
    """用學號打招呼"""
    return f"你好，同學 {student_id}！歡迎完成第10週作業。"
