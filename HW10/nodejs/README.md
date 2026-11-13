# hello-week10

第10週作業範例套件（Node.js / npm）

## 安裝

```bash
npm install hello-week10-yourname
```

> 請將 `yourname` 替換成實際發佈時使用的套件名稱。

## 使用方式

```js
const { hello, add, greetStudent } = require("hello-week10-yourname");

console.log(hello("小明"));
// Hello, 小明! This is HW10 Node.js package.

console.log(add(3, 5));
// 8

console.log(greetStudent("B12345678"));
// 你好，同學 B12345678！歡迎完成第10週作業。
```

## API

| 函式 | 說明 | 範例 |
|------|------|------|
| `hello(name = "World")` | 回傳問候語 | `hello("小明")` |
| `add(a, b)` | 兩數相加 | `add(3, 5)` → `8` |
| `greetStudent(studentId)` | 用學號打招呼 | `greetStudent("B12345678")` |

## License

MIT
