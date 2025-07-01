# Producer-Worker 架構說明

此文件記錄 `producer_104.py` 與 `task_104.py` 之間的分工與協作模式，此模式為典型的「生產者/消費者」(Producer/Consumer) 架構。

---

### 基本概念

- **Producer (生產者)**: 負責產生任務並將其放入一個共享的「任務佇列」(Task Queue) 中。
- **Worker (消費者/執行者)**: 從任務佇列中取出任務並執行。

在我們的專案中：
- `producer_104.py` 扮演 **Producer** 的角色。
- `task_104.py` 中定義的 Celery task (`process_single_job_data`) 扮演 **Worker** 的角色。

--- 

### Producer (`producer_104.py`) 的角色：任務的產生者與分派者

`producer_104.py` 的核心職責是**產生任務清單**。它本身不處理任何單一職缺的詳細資料，而是專注於：

1.  **探索與搜尋**:
    - 根據設定的關鍵字 (`KEYWORDS`) 和職業類別 (`JOBCAT_CODE`) 去呼叫 104 的**職缺列表 API** (`/jobs/search/api/jobs`)。
    - 遍歷搜尋結果的所有頁面，以找出所有符合條件的職缺。

2.  **收集與過濾**:
    - 從搜尋結果中，僅提取每個職缺的**專屬連結 (URL)**。
    - 使用 `set()` 結構來確保收集到的 URL 都是獨一無二的，避免重複派發同一個任務。

3.  **分派任務 (發送網址)**:
    - 遍歷所有收集到的獨立 URL。
    - 對於每一個 URL，它會呼叫 `process_single_job_data.delay(url)`。這個 `.delay()` 是關鍵，它並非直接執行函式，而是將一個「任務」（包含 `job_url` 這個參數）發送到 Celery 的任務佇列中 (例如 RabbitMQ)。

**總結：Producer 就像一位「專案經理」，負責找出所有需要完成的工作，然後把工作項目（職缺 URL）一個個地交辦下去。**

---

### Worker (`task_104.py`) 的角色：任務的實際執行者

`task_104.py` 中定義的 `@app.task` (`process_single_job_data`) 就是 Worker 要執行的具體工作。它的職責是**專心處理好單一任務**：

1.  **接收任務**:
    - Celery Worker 會從任務佇列中取出一個由 Producer 發送過來的任務。這個任務的內容就是一個 `job_url`。

2.  **抓取詳細資料 (收集網址資料)**:
    - Worker 使用收到的 `job_url`，呼叫 `fetch_104_job_data` 函式。
    - 這個函式會去請求**職缺內容 API** (`/job/ajax/content/...`)，抓取這**一個**職缺所有詳細的 JSON 資料。

3.  **處理與儲存**:
    - 抓取到資料後，Worker 會進行資料清理 (`remove_illegal_chars`)、轉換成 DataFrame。
    - 最後，將處理好的乾淨資料儲存成 `.csv` 檔案，或上傳到資料庫。

**總結：Worker 就像是「執行者」，它不需要知道總共有多少工作，也不需要知道工作的來源，只要專心處理好手上這一個 URL 就好。**

---

### 為什麼要這樣分工？

這種架構帶來了幾個關鍵優勢：

- **擴展性 (Scalability)**: 當處理速度需要提升時，我們無需修改程式碼，只需啟動更多的 Worker 實例。這些 Worker 會自動從佇列中領取任務並行處理，實現水平擴展。
- **解耦合 (Decoupling)**: Producer 和 Worker 的職責完全分離。修改搜尋邏輯只需更動 Producer，而修改資料儲存方式只需更動 Worker，兩者互不干擾，提高了系統的可維護性。
- **可靠性 (Reliability)**: 如果某個 Worker 在處理單一任務時失敗或崩潰，它不會影響到 Producer 或其他正在運行的 Worker。佇列中的任務依然存在，可以被重啟的 Worker 或其他健康的 Worker 重新領取並處理，確保了任務不會遺失。
