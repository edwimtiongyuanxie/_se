# hello-week10 (Rust / crates.io)

這是第10週作業的 Rust 套件範例。

## 使用方式（發佈後）

在你的 `Cargo.toml` 加入：

```toml
[dependencies]
hello-week10-yourname = "0.1.0"
```

然後在程式中：

```rust
use hello_week10_yourname::{hello, add, greet_student};

fn main() {
    println!("{}", hello("小明"));
    println!("{}", add(3, 5));
    println!("{}", greet_student("B12345678"));
}
```

## 發佈到 crates.io 步驟

### 1. 安裝 Rust（如果還沒裝）

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### 2. 修改套件名稱（很重要！）

打開 `Cargo.toml`，把 `name = "hello-week10-yourname"` 改成**全域唯一**的名稱，例如：

```toml
name = "hello-week10-b12345678"
```

注意：Rust 套件名稱只能使用小寫字母、數字、`-` 和 `_`。

### 3. 註冊帳號並取得 Token

1. 到 https://crates.io 註冊（可用 GitHub 登入）
2. 到 https://crates.io/settings/tokens 產生 API Token

### 4. 登入並發佈

```bash
# 進入此資料夾
cd rust

# 登入（貼上你的 token）
cargo login

# 檢查是否能通過編譯與測試
cargo test

# 發佈
cargo publish
```

### 5. 驗證

到 https://crates.io/crates/你的套件名稱 確認是否成功出現。

## 常用指令

```bash
# 執行測試
cargo test

# 檢查程式碼
cargo check

# 產生文件
cargo doc --open
```

## 注意事項

- 套件名稱一旦發佈就無法刪除（只能 yank）
- 發佈前請確認 `cargo test` 全部通過
- 不要把 Token commit 到 GitHub
