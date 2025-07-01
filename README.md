# 104 人力銀行職缺爬蟲系統 - 使用手冊

本系統是一個基於 Docker 和 Celery 的分散式爬蟲，專門用於抓取 104 人力銀行的職缺資料。它會將資料儲存於 MySQL 資料庫，並透過 FastAPI 提供 API 接口進行查詢。

## 系統架構

系統由以下幾個核心服務組成，透過 `docker-compose.yml` 進行統一管理：

-   **MySQL (`mysql`)**: 核心資料庫，用於儲存所有爬取到的資料，包括職缺類別、URL 和詳細資訊。
-   **RabbitMQ (`rabbitmq`)**: 訊息代理，負責接收任務指令並分派給 Celery Worker。
-   **Celery Worker (`worker-104`)**: 執行爬蟲任務的背景工作單元，負責實際的資料抓取與處理。
-   **Producers (`producer-*`)**: 一次性的觸發腳本，用於向 RabbitMQ 發送不同階段的爬蟲任務。
-   **FastAPI (`api`)**: 提供一個 RESTful API 接口，讓使用者可以方便地查詢已存入資料庫的職缺資料。
-   **Flower (`flower`)**: Celery 的監控儀表板，用於即時查看任務執行狀況。
-   **phpMyAdmin**: MySQL 的網頁管理介面，方便直接操作資料庫。

## 資料處理流程

本系統的資料處理流程主要分為三個階段，由使用者手動觸發：

1.  **抓取職缺類別 (Category)**
    -   **觸發**: `producer-category`
    -   **流程**:
        -   從 104 網站獲取所有職缺的分類代碼與名稱。
        -   資料會快取在容器內的 `/home/app_user/data/104_人力銀行_category.csv` 以減少重複請求。
        -   處理後的分類資料儲存至資料庫的 `tb_category` 表格。

2.  **抓取職缺 URL 列表 (URL List)**
    -   **觸發**: `producer-urls`
    -   **流程**:
        -   根據 `.env` 檔案中設定的 `JOBCAT_CODE` (職缺類別) 和 `KEYWORDS` (關鍵字)。
        -   併發地爬取 104 的搜尋結果頁面，收集所有符合條件的職缺 URL。
        -   將不重複的 URL 儲存至資料庫的 `tb_urls` 表格。

3.  **抓取職缺詳細內容 (Job Details)**
    -   **觸發**: `producer-job-details`
    -   **流程**:
        -   從 `tb_urls` 表格讀取所有待處理的 URL。
        -   併發地請求每個職缺的 AJAX API，獲取詳細的 JSON 資料。
        -   將解析並清理過的資料儲存至資料庫的 `tb_jobs` 表格。

## 操作說明

### 步驟 1: 環境設定

在專案根目錄下，建立一個名為 `.env` 的檔案。此檔案用於存放所有服務的環境變數。

您可以複製以下範本，並根據您的需求修改：

```env
# .env

# --- MySQL Database Configuration ---
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=job_data
MYSQL_USER=user
MYSQL_PASSWORD=password
MYSQL_HOST=mysql
MYSQL_PORT=3306

# --- RabbitMQ Configuration ---
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672

# --- 104 Crawler Specific Settings ---
# 職缺類別代碼 (例如: 2007000000 代表軟體及工程相關類)
JOBCAT_CODE=2007000000
# 搜尋關鍵字 (用逗號分隔)
KEYWORDS=Python,Golang,Java,Backend
# 每個關鍵字要爬取的最大頁數
MAX_PAGES=100
# 排序方式 (15: 符合度, 16: 最近更新)
ORDER_SETTING=15
```

### 步驟 2: 啟動所有服務

在專案根目錄下，執行以下指令來建置映像檔並在背景啟動所有服務：

```bash
docker compose up --build -d
```

### 步驟 3: 執行爬蟲任務

服務啟動後，您可以依照資料流程，依序執行以下指令來觸發各階段的爬蟲任務。

**1. 抓取職缺類別 (可選，但建議初次執行時運行)**

```bash
docker compose run --rm producer-category
```

**2. 抓取職缺 URL 列表**

```bash
docker compose run --rm producer-urls
```

**3. 抓取職缺詳細內容**

```bash
docker compose run --rm producer-job-details
```

### 步驟 4: 查詢已抓取的資料

爬蟲任務完成後，資料將存入 MySQL。您可以透過 `api` 服務提供的接口進行查詢。

-   **API 根目錄**: [http://localhost:8000/](http://localhost:8000/)
-   **API 文件 (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)


**查詢範例 (使用 curl):**

查詢職稱包含 "Python" 的前 10 筆職缺：

```bash
curl -X GET "http://localhost:8000/jobs/?title=Python&limit=10"
```

查詢公司名稱包含 "新加坡商" 的職缺：

```bash
curl -X GET "http://localhost:8000/jobs/?company_name=新加坡商"
```

## 監控與管理

系統提供多個網頁儀表板，方便您監控服務狀態：

-   **Flower (Celery 監控)**: [http://localhost:5555](http://localhost:5555)
-   **RabbitMQ Management**: [http://localhost:15672](http://localhost:15672) (帳號/密碼: guest/guest)
-   **phpMyAdmin (資料庫管理)**: [http://localhost:8080](http://localhost:8080)

## 停止服務

若要停止所有服務，請執行：

```bash
docker compose down
```

如果您希望在停止時一併刪除所有資料（包括 MySQL 資料庫和 RabbitMQ 的訊息），請加上 `-v` 參數：

```bash
docker compose down -v
```
