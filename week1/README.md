# week1：簡易命令列 HTTP 客戶端（pycurl）

只用 Python 3 標準函式庫（`urllib`、`http.client`）寫成的 curl 風格 HTTP 客戶端。不需要安裝任何套件。

A curl-like command-line HTTP client. Python 3 standard library only — no installs.

## 環境

- Python 3.9 或更新版本
- 不使用 pip、虛擬環境或第三方套件

## 用法

在儲存庫根目錄執行：

```bash
python3 week1/pycurl.py [選項] URL
```

也可以先加上執行權限，再直接執行：

```bash
chmod +x week1/pycurl.py
./week1/pycurl.py [選項] URL
```

成功時，回應內容寫到標準輸出，結束狀態為 `0`。失敗時結束狀態不為 `0`（參數錯誤為 `2`，其餘為 `1`）。`-v` 的請求／回應行寫到標準錯誤，不會混進內容。

## 選項

| 選項 | 說明 |
| --- | --- |
| `URL` | 必填。只接受 `http` 與 `https`。片段（`#...`）不會送到伺服器。 |
| `-X, --request METHOD` | HTTP 方法。預設 `GET`；若有 `-d` 且未指定方法，則為 `POST`。方法會轉成大寫。支援 `GET`、`POST`、`PUT`、`DELETE`、`HEAD`、`PATCH`，其他合法方法名稱也可以。 |
| `-H, --header HEADER` | 請求標頭，格式 `Name: value`，可重複。同名標頭會依序全部送出。`-H "Name:"`（值為空）會移除該標頭，包含預設的 `Accept`。 |
| `-d, --data DATA` | 請求內容，可重複，多段以 `&` 連接。`@檔案` 以二進位原樣讀取；`@-` 從標準輸入讀取。未自行指定 `Content-Type` 時，預設為 `application/x-www-form-urlencoded`。字串以 UTF-8 編碼。 |
| `-i, --include` | 在內容之前印出狀態行與回應標頭。 |
| `-I, --head` | 改送 `HEAD`，只輸出回應標頭，不送出內容。 |
| `-o, --output FILE` | 把原本要印到標準輸出的內容寫入檔案（覆寫）。 |
| `-L, --location` | 跟隨 `301`、`302`、`303`、`307`、`308`。最多 20 次。 |
| `-v, --verbose` | 在標準錯誤印出連線訊息，以及 `>` 請求行、`<` 回應行。 |
| `-s, --silent` | 不印錯誤訊息。內容仍會輸出，結束狀態仍反映成功或失敗。`-v` 不受影響。 |
| `--timeout SECONDS` | 連線與讀取的逾時秒數，可以是小數。未指定則一直等待。 |

預設還會送出 `Host`、`User-Agent: pycurl/1.0`、`Accept: */*`、`Connection: close`。有內容時會自動加上正確的 `Content-Length`。

### 重新導向

未加 `-L` 時，`3xx` 會原樣輸出（結束狀態為 0，因為狀態碼小於 400）。加上 `-L` 之後：

- `301`、`302`：若原方法是 `POST`，改成 `GET` 並捨棄內容與 `Content-Type`。
- `303`：除了 `HEAD` 以外都改成 `GET`，並捨棄內容。
- `307`、`308`：方法與內容都保留。
- 沒有 `Location`，或超過 20 次，就停止。超過上限時結束狀態為 `1`，且不輸出中間回應。

### 結束狀態

| 狀態 | 時機 |
| --- | --- |
| `0` | 傳輸完成，且 HTTP 狀態小於 400。 |
| `1` | 連線失敗、逾時、HTTP 4xx/5xx、重新導向過多、讀寫檔案失敗、不支援的網址。回應內容仍會輸出（除非連線在收到回應前就失敗）。 |
| `2` | 參數不合法，例如缺少 URL、方法或標頭格式錯誤、`--timeout` 為負數。 |

這和 curl 預設不同：curl 遇到 404 仍回傳 0，除非加上 `--fail`。這個客戶端把 HTTP 錯誤視為失敗，但**仍會印出錯誤頁的內容**，方便查看。

## 範例

先在另一個終端機，於本專案目錄啟動 Python 內建的靜態伺服器：

```bash
python3 -m http.server 8000
```

```bash
# GET，內容印到終端機
python3 week1/pycurl.py http://127.0.0.1:8000/

# 連同狀態行與回應標頭一起印出
python3 week1/pycurl.py -i http://127.0.0.1:8000/

# 只取標頭（HEAD）
python3 week1/pycurl.py -I http://127.0.0.1:8000/

# 詳細模式：請求／回應行在標準錯誤，內容在標準輸出
python3 week1/pycurl.py -v http://127.0.0.1:8000/week1/README.md

# 存檔，並跟隨重新導向
python3 week1/pycurl.py -L -o page.html http://127.0.0.1:8000/

# 逾時 5 秒；-s 關掉錯誤文字，結束狀態仍可用 $? 判斷
python3 week1/pycurl.py -s --timeout 5 http://127.0.0.1:8000/
echo $?
```

送出 JSON、表單與檔案（請把網址換成會接收 POST 的服務）：

```bash
python3 week1/pycurl.py \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"name":"測試"}' \
  https://example.com/api

python3 week1/pycurl.py -d "name=ada" -d "lang=zh" https://example.com/form

python3 week1/pycurl.py -d @body.txt -o response.bin https://example.com/upload

python3 week1/pycurl.py -X PUT -d @notes.txt https://example.com/items/1
python3 week1/pycurl.py -X PATCH -H "Content-Type: application/json" -d '{"ok":true}' https://example.com/items/1
python3 week1/pycurl.py -X DELETE https://example.com/items/1
```

從標準輸入讀取內容：

```bash
printf 'hello' | python3 week1/pycurl.py -d @- https://example.com/echo
```

## 測試

測試只用本機的 `http.server`，不連外網：

```bash
python3 -m unittest discover -s week1 -v
```

也可以：

```bash
python3 week1/test_pycurl.py
```

## 限制

- 僅 `http` 與 `https`。`https` 使用系統憑證，不能關閉驗證。
- 網址裡的帳號密碼不會被當成 Basic 認證送出。
- 沒有 cookie、proxy、multipart 表單、HTTP/2，也不會重用連線。
- 標頭值必須是 Latin-1（HTTP 的限制）。中文請放在內容，不要放在標頭。
- 請求與回應內容會整段讀進記憶體。

## English

`week1/pycurl.py` is a small curl-like HTTP client (stdlib only).

```bash
python3 week1/pycurl.py [-X METHOD] [-H "Name: value"] [-d DATA|@file|@-] \
  [-i] [-I] [-o FILE] [-L] [-v] [-s] [--timeout SECONDS] URL
```

- Default method is GET, or POST when `-d` is set. `-d` pieces join with `&`. `@file` is sent unchanged; `@-` reads stdin.
- `-i` prints response headers before the body. `-I` sends HEAD and prints headers only. `-o` writes that output to a file.
- `-L` follows 301/302/303/307/308 (at most 20). 301/302 turn POST into GET; 303 turns any method except HEAD into GET; 307/308 keep the method and body.
- `-v` logs request (`>`) and response (`<`) lines on stderr. `-s` hides error text only.
- Exit `0` means HTTP status below 400. Exit `1` is a transfer failure, timeout, or HTTP 4xx/5xx (the body is still written). Exit `2` is bad usage.

```bash
python3 -m unittest discover -s week1 -v
```
