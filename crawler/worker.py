# crawler/worker.py
"""
Celery Worker 啟動腳本。

這是 Celery Worker 進程的進入點。它負責：
1. 初始化應用程式級別的配置 (如日誌)。
2. 導入共享的 Celery App 實例。
3. 在 Worker 啟動時，確保資料庫和表格都已準備就緒。
"""

import logging
from . import logging_config

# 1. 執行應用程式級別的配置
# 必須在所有應用程式邏輯導入之前執行，以確保日誌格式統一。
logging_config.setup_logging()
logger = logging.getLogger(__name__)

# 2. 導入共享的 Celery App 實例
# 這是關鍵步驟。所有 Worker 都從同一個 app 定義啟動。
from .app import app

# 3. 在 Worker 啟動時，初始化資料庫連接並確保表格存在
try:
    from .database.connection import initialize_database_tables

    logger.info("Worker process starting, ensuring database is initialized...")
    initialize_database_tables()
    logger.info("Database initialization check complete.")
except Exception as e:
    logger.critical(
        f"Database initialization failed on worker startup: {e}", exc_info=True
    )
    # 在生產環境中，你可能希望在這裡退出，因為沒有資料庫 Worker 也無法工作。
    # import sys
    # sys.exit(1)

# --- 診斷代碼 ---
# 在 Worker 配置完成後，打印所有已註冊的任務，方便調試。
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """日誌記錄所有已註冊的 Celery 任務。"""
    logger.info("Celery Worker configured. Listing all registered tasks:")
    task_names = sorted(sender.tasks.keys())
    for task_name in task_names:
        # 任務名稱是透過 'name' 參數或自動生成的模組路徑
        logger.info(f"  - Registered Task: {task_name}")

# 注意：我們不再需要手動導入任何任務模組。
# Celery 會根據 app.py 中的 `include` 列表自動發現並註冊它們。
# 這使得 worker.py 成為一個通用的啟動器，無需關心具體的任務實現。