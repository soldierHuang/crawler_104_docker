# crawler/config.py
"""
此模組包含應用程式的通用配置設定，例如資料庫和訊息佇列的連線資訊。
這些設定是整個爬蟲系統通用的，不應僅限於特定專案。

透過 .env 檔案載入環境變數，實現設定與程式碼的分離。
"""

import os
from dotenv import load_dotenv
from typing import Final

# 在模組導入時，僅載入一次 .env 檔案
load_dotenv()

# --- MySQL Database Configuration ---
MYSQL_HOST: Final[str] = os.environ.get("MYSQL_HOST", "mysql")
MYSQL_PORT: Final[int] = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_ACCOUNT: Final[str] = os.environ.get("MYSQL_USER", "user")
MYSQL_PASSWORD: Final[str] = os.environ.get("MYSQL_PASSWORD", "password")
MYSQL_DATABASE: Final[str] = os.environ.get("MYSQL_DATABASE", "job_data")

# --- RabbitMQ Configuration (for Celery) ---
# 使用與 RabbitMQ Docker 容器相同的環境變數名稱，確保設定的一致性，避免驗證錯誤。
# 這是解決 'AccessRefused' 錯誤的關鍵。
RABBITMQ_HOST: Final[str] = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT: Final[int] = int(os.environ.get("RABBITMQ_PORT", "5672"))
RABBITMQ_DEFAULT_USER: Final[str] = os.environ.get("RABBITMQ_DEFAULT_USER", "guest")
RABBITMQ_DEFAULT_PASS: Final[str] = os.environ.get("RABBITMQ_DEFAULT_PASS", "guest")