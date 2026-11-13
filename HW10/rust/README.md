# hello-week10

第10週作業範例套件（Rust / crates.io）

## 安裝

在你的 `Cargo.toml` 中加入：

```toml
[dependencies]
hello-week10-yourname = "0.1.0"
```

> 請將 `yourname` 替換成實際發佈時使用的套件名稱。

## 使用方式

```rust
use hello_week10_yourname::{hello, add, greet_student};

fn main() {
    println!("{}", hello("小明"));
    // Hello, 小明! This is HW10 Rust package.

    println!("{}", add(3, 5));
    // 8

    println!("{}", greet_student("B12345678"));
    // 你好，同學 B12345678！歡迎完成第10週作業。
}
```

## API

| 函式 | 說明 | 範例 |
|------|------|------|
| `hello(name: &str) -> String` | 回傳問候語 | `hello("小明")` |
| `add(a: i32, b: i32) -> i32` | 兩數相加 | `add(3, 5)` → `8` |
| `greet_student(student_id: &str) -> String` | 用學號打招呼 | `greet_student("B12345678")` |

## License

MIT
