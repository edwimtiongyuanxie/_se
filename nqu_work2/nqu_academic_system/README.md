# 國立金門大學 校務資訊系統 (Demo)

這是一個模擬**國立金門大學校務資訊系統**的教學專案，實作學生端常用功能。

## 功能特色

| 功能 | 說明 |
|------|------|
| 學生登入 | 學號 + 密碼登入（模擬真實系統） |
| 個人資料 | 查看學號、姓名、系所、年級、聯絡方式 |
| 選課作業 | 瀏覽開課清單、選課 / 檢查名額 |
| 我的課表 | 已選課程清單 + 簡易週課表 |
| 成績查詢 | 歷年成績、GPA 計算 |
| 請假申請 | 線上請假 + 申請紀錄查詢 |

## 技術架構

- **後端**：Python Flask
- **資料庫**：SQLite
- **前端**：Bootstrap 5 + Bootstrap Icons
- **密碼**：Werkzeug 雜湊儲存

## 快速啟動

```bash
# 1. 進入專案目錄
cd nqu_academic_system

# 2. 安裝套件
pip install -r requirements.txt

# 3. 執行
python app.py
```

開啟瀏覽器前往：http://127.0.0.1:5000

## 測試帳號

| 學號 | 密碼 | 姓名 | 系所 |
|------|------|------|------|
| 11201001 | 1234 | 王小明 | 資訊工程學系 |
| 11202015 | 5678 | 陳美華 | 企業管理學系 |
| 11303008 | 9012 | 林志豪 | 觀光管理學系 |
| 11104022 | 3456 | 張雅婷 | 護理學系 |

## 專案結構

```
nqu_academic_system/
├── app.py                 # 主程式（路由 + 資料庫）
├── requirements.txt
├── README.md
├── nqu_system.db          # 執行後自動產生
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── courses.html
│   ├── my_courses.html
│   ├── grades.html
│   └── leave.html
└── static/                # 可放自訂 CSS/圖片
```

## 對應真實系統功能

本 Demo 對應金門大學實際校務系統常見作業：

- 選課作業
- 課表查詢
- 成績查詢
- 學生請假作業
- 個人資料 / 學籍記載表

僅供**習題 / 教學示範**使用，非正式校務系統。
