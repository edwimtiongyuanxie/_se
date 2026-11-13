# HW10 - 公開套件發佈範例

第10週作業：將套件發佈到公開套件庫

| 語言     | 套件庫     | 資料夾   | 狀態說明           |
|----------|------------|----------|--------------------|
| Python   | PyPI       | `python/`  | 最推薦，最容易成功 |
| Node.js  | npm        | `nodejs/`  | 簡單快速           |
| Rust     | crates.io  | `rust/`    | 需先安裝 Rust      |

---

## 使用方式

1. 把這個資料夾上傳到自己的 GitHub Repository（建議命名 `HW10`）
2. 依照各資料夾內的 `README.md` 操作
3. 發佈成功後，把套件網址貼到作業繳交區

---

## 重要提醒

- **套件名稱必須是全域唯一**，建議加上自己的學號或名字，例如：
  - `hello-week10-b12345678`
  - `hello-week10-yourname`
- 正式發佈前建議先用 **TestPyPI** / **npm 的 dry-run** 測試
- 不要把 API Token 或密碼 commit 到 GitHub

---

## 資料夾結構

```
HW10/
├── README.md                 ← 你現在看的這個檔案
├── python/                   ← Python + PyPI 範例
│   ├── pyproject.toml
│   ├── README.md
│   └── src/hello_week10/
│       └── __init__.py
├── nodejs/                   ← Node.js + npm 範例
│   ├── package.json
│   ├── index.js
│   └── README.md
└── rust/                     ← Rust + crates.io 範例
    ├── Cargo.toml
    ├── src/lib.rs
    └── README.md
```
