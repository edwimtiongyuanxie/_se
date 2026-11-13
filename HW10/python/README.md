# hello-week10

第10週作業範例套件（Python / PyPI）

## 安裝

```bash
pip install hello-week10-YOURNAME
```

> 請將 `YOURNAME` 替換成實際發佈時使用的套件名稱。

## 使用方式

```python
from hello_week10 import hello, add, greet_student

print(hello("小明"))
# Hello, 小明! This is HW10 Python package.

print(add(3, 5))
# 8

print(greet_student("B12345678"))
# 你好，同學 B12345678！歡迎完成第10週作業。
```

## API

| 函式 | 說明 | 範例 |
|------|------|------|
| `hello(name="World")` | 回傳問候語 | `hello("小明")` |
| `add(a, b)` | 兩數相加 | `add(3, 5)` → `8` |
| `greet_student(student_id)` | 用學號打招呼 | `greet_student("B12345678")` |

## License

MIT
