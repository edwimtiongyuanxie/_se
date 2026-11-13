# HW10 - 公開套件發佈範例

第10週作業：將套件發佈到公開套件庫

| 語言     | 套件庫     | 資料夾   | 發佈後網址範例 |
|----------|------------|----------|----------------|
| Python   | PyPI       | `python/`  | https://pypi.org/project/hello-week10-YOURNAME |
| Node.js  | npm        | `nodejs/`  | https://www.npmjs.com/package/hello-week10-yourname |
| Rust     | crates.io  | `rust/`    | https://crates.io/crates/hello-week10-yourname |

---

## 專案結構

```
HW10/
├── README.md                 ← 本檔案（GitHub 說明）
├── LICENSE
├── .gitignore
├── python/                   ← Python 套件（發佈到 PyPI）
│   ├── pyproject.toml
│   ├── README.md             ← 套件說明（發佈後會顯示在 PyPI）
│   └── src/hello_week10/
│       └── __init__.py
├── nodejs/                   ← Node.js 套件（發佈到 npm）
│   ├── package.json
│   ├── index.js
│   └── README.md             ← 套件說明（發佈後會顯示在 npm）
└── rust/                     ← Rust 套件（發佈到 crates.io）
    ├── Cargo.toml
    ├── src/lib.rs
    └── README.md             ← 套件說明（發佈後會顯示在 crates.io）
```

---

## 發佈前必做

1. 把三個套件的名稱改成**全域唯一**（建議加上學號）：
   - `python/pyproject.toml` → `name = "hello-week10-b12345678"`
   - `nodejs/package.json` → `"name": "hello-week10-b12345678"`
   - `rust/Cargo.toml` → `name = "hello-week10-b12345678"`

2. 修改作者資訊與 GitHub 連結

3. 依照各語言的發佈流程上傳套件

---

## 發佈後

發佈成功後，請把三個套件的網址貼到作業繳交區。
