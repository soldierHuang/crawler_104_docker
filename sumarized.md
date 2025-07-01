Docker 容器化爬蟲專案測試 SOP

驗證整個爬蟲系統（資料庫、訊息佇列、Worker、Producers）在 Docker 環境下能正確協同工作，完成從「觸發任務」到「資料入庫」的完整流程。

Phase 1: 準備工作 (Preparation)
在啟動任何服務前，確保您的開發環境是乾淨且配置正確的。
步驟 1.1：檢查環境與配置
1.1.1 確認 Docker 已安裝並運行：
docker --version
docker compose version

1.1.2 確認 .env 檔案：
在專案根目錄下，確保 .env 檔案存在且內容正確。


<!-- 步驟 1.2：清理舊環境 (非常重要！)
為了避免舊的資料卷 (volumes) 或網路設定干擾測試，請執行以下指令進行徹底清理：
* 目的：確保每次測試都在一個全新的、可預期的「乾淨」環境中開始。
# 停止並移除所有相關容器、網路，並刪除資料卷(-v)
docker compose down --volumes --remove-orphans -->


Phase 2: 建置並啟動與驗證 (Startup & Verification)
現在，我們將啟動整個系統，並驗證每個核心服務是否健康。
- 步驟 2.1：建置映像檔以確保一切都是最新的
docker compose build

- 步驟 2.2：啟動所有服務
# 在背景模式(-d)下啟動所有服務
docker compose up -d
<!-- 關閉服務
docker compose down -->

- 步驟 2.3：檢查容器狀態
等待約 30 秒讓服務完成啟動，然後執行：
# 列出所有服務的容器狀態
docker compose ps
驗證方法：您應該看到所有服務的 STATUS 都是 running 或 healthy。
如果任何容器處於 exited 或 restarting 狀態，說明啟動失敗，需要立即檢查日誌。

- 步驟 2.4：檢查 Worker 初始化日誌
這是驗證 Worker 是否成功連接到 RabbitMQ 和 MySQL 的關鍵步驟。

# 查看 worker-104 服務的最後 50 行日誌
docker compose logs --tail=50 worker-104

驗證方法：在日誌中尋找以下關鍵訊息：
Database initialization check complete. (表示已成功連接 MySQL)
Connected to amqp://... (表示已成功連接 RabbitMQ)
Registered Task: crawler.project_104.task_category_104.process_category_data
Registered Task: crawler.project_104.task_job_details_104.fetch_and_save_all
Registered Task: crawler.project_104.task_urls_104.fetch_and_save_all_urls
看到這些訊息，代表 Worker 已準備就緒，可以接收任務。

步驟 2.5：驗證 Web 管理介面
RabbitMQ: 打開瀏覽器訪問 http://localhost:15672
使用 .env 中設定的 RABBITMQ_DEFAULT_USER 和 RABBITMQ_DEFAULT_PASS 登入。
驗證：在 "Queues" 分頁中，您應該能看到一個名為 worker_104 的隊列。
Flower (Celery 監控): 打開瀏覽器訪問 http://localhost:5555
驗證：您應該能看到一個名為 worker-104 的 worker 在線 (Online)。
phpMyAdmin: 打開瀏覽器訪問 http://localhost:8000
使用 .env 中設定的 MYSQL_USER 和 MYSQL_PASSWORD 登入。
驗證：您應該能成功登入，並在左側看到 job_data 資料庫，裡面有 tb_jobs, tb_urls, tb_category 三個空的資料表。


Phase 3: 執行爬蟲任務 (Executing the Crawler Tasks)
系統已健康運行，現在我們要像一個使用者一樣，觸發爬蟲任務。我們將通過 docker compose exec 指令在 worker-104 容器內執行 producer 腳本。
步驟 3.1：觸發「職位類別」抓取任務
# 在 worker-104 容器中，執行 producer_category 模組
docker compose exec worker-104 python -m crawler.project_104.producer_category

監控與驗證：
Flower: 刷新 http://localhost:5555，您應該能在 "Tasks" 分頁看到一個 process_category_data 任務，狀態最終變為 Succeeded。
phpMyAdmin: 刷新 tb_category 資料表，您應該能看到滿滿的職位類別資料。

步驟 3.2：觸發「職缺 URL 列表」抓取任務
# 在 worker-104 容器中，執行 producer_urls 模組
docker compose exec worker-104 python -m crawler.project_104.producer_urls

監控與驗證：
Flower: 您會看到一個 fetch_and_save_all_urls 任務出現並執行。
phpMyAdmin: 刷新 tb_urls 資料表，您應該能看到根據您的關鍵字抓取到的職缺 URL。


步驟 3.3：觸發「職缺詳細內容」抓取任務
# 在 worker-104 容器中，執行 producer_job_details 模組
docker compose exec worker-104 python -m crawler.project_104.producer_job_details
監控與驗證：
Flower: 您會看到一個 fetch_and_save_all 任務出現。這個任務會花費較長時間。
Worker Logs: 您可以透過 docker compose logs -f worker-104 實時觀察進度日誌。
phpMyAdmin: 刷新 tb_jobs 資料表，您會看到職缺詳細資料被分批次地寫入。



<!-- 步驟 4 Dockerfile 進階版   docker-compose_v2.yml

Phase 4.1: 啟動核心服務 「背景服務」
docker compose up -d mysql rabbitmq phpmyadmin flower worker-104

Phase 4.2: 觸發任務
# --rm 會在容器執行完畢後自動刪除它，保持環境乾淨
觸發「職位類別」抓取：
docker compose run --rm producer-category

觸發「職缺 URL」抓取：
docker compose run --rm producer-urls

觸發「職缺詳細內容」抓取：
docker compose run --rm producer-job-details -->


步驟 5  Dockerfile 微服務

# 注意，末尾的 "." 代表使用當前目錄的 Dockerfile
Phase 5.1 建立 docker image  與 查詢
docker build -t benitorhuang/crawler_104:latest -t benitorhuang/crawler_104:0.0.1 .
docker images 


Phase 5.2 推送 docker image # 用戶名/image_name:版號
docker push benitorhuang/crawler_104:0.0.1

Phase 5.3 建立 producer 微服務 yml 檔案
pruducer.producer.yml

Phase 5.4 啟用背景服務 + producer 發送任務
docker compose up -d
docker compose -f pruducer.producer.yml 
核心指令格式：
docker compose -f <yml檔案名> run --rm <服務名>


# 觸發 category 任務
docker compose -f docker-compose.producer.yml run --rm producer-category

# 觸發 urls 任務
docker compose -f docker-compose.producer.yml run --rm producer-urls

# 觸發 job details 任務
docker compose -f docker-compose.producer.yml run --rm producer-job-details

