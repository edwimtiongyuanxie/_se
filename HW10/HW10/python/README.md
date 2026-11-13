# hello-week10 (Python / PyPI)

這是第10週作業的 Python 套件範例。

## 安裝（發佈後）

```bash
pip install hello-week10-YOURNAME
```

## 使用範例

```python
from hello_week10 import hello, add, greet_student

print(hello("小明"))
print(add(3, 5))
print(greet_student("B12345678"))
```

## 發佈到 PyPI 步驟

### 1. 修改套件名稱（很重要！）

打開 `pyproject.toml`，把 `name = "hello-week10-YOURNAME"` 改成**全域唯一**的名稱，例如：

```toml
name = "hello-week10-b12345678"
```

同時修改 `authors` 和 `Homepage` 的連結。

### 2. 註冊帳號

- 正式環境：https://pypi.org/account/register/
- 測試環境（建議先用）：https://test.pypi.org/account/register/

### 3. 產生 API Token

到 https://pypi.org/manage/account/token/ 產生 Token（建議 scope 選「Entire account」或特定專案）。

### 4. 建置與上傳

```bash
# 進入此資料夾
cd python

# 安裝工具
pip install build twine

# 建置
python -m build

# 先上傳到 TestPyPI 測試（強烈建議）
twine upload --repository testpypi dist/*

# 確認沒問題後，再上傳到正式 PyPI
twine upload dist/*
```

上傳時會要求輸入：
- Username：`__token__`
- Password：你的 API Token（以 `pypi-` 開頭）

### 5. 驗證

到 https://pypi.org/project/你的套件名稱/ 確認是否成功出現。

## 注意事項

- 套件名稱一旦發佈就無法刪除（只能 yank），請謹慎選擇名稱
- 不要把 Token 寫進程式碼或 commit 到 GitHub
