# hello-week10 (Node.js / npm)

這是第10週作業的 Node.js 套件範例。

## 安裝（發佈後）

```bash
npm install hello-week10-yourname
```

## 使用範例

```js
const { hello, add, greetStudent } = require("hello-week10-yourname");

console.log(hello("小明"));
console.log(add(3, 5));
console.log(greetStudent("B12345678"));
```

## 發佈到 npm 步驟

### 1. 修改套件名稱（很重要！）

打開 `package.json`，把 `"name": "hello-week10-yourname"` 改成**全域唯一**的名稱，例如：

```json
"name": "hello-week10-b12345678"
```

同時修改 `author` 和 `repository` 的資訊。

### 2. 註冊帳號

到 https://www.npmjs.com/signup 註冊。

### 3. 登入並發佈

```bash
# 進入此資料夾
cd nodejs

# 登入（會開啟瀏覽器或要求輸入帳密）
npm login

# 發佈（公開套件）
npm publish --access public
```

如果是第一次發佈 scoped 套件（名稱以 `@username/` 開頭），也需要加 `--access public`。

### 4. 驗證

到 https://www.npmjs.com/package/你的套件名稱 確認是否成功出現。

## 常用指令

```bash
# 測試本地功能
npm test

# 檢查套件內容（不會真的發佈）
npm publish --dry-run
```

## 注意事項

- 套件名稱一旦發佈就無法完全刪除（24小時內可 unpublish）
- 建議先用 `npm publish --dry-run` 確認內容正確
