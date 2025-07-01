# crawler/app.py
"""
Celery Application Definition.

此模組負責創建和配置 Celery 應用程式實例。
所有的 tasks 和 worker 都應該從此模組導入 `app` 物件，
以確保一致性並避免循環導入問題。
"""

from celery import Celery
from . import config

# 建立 Celery 應用程式實例
app = Celery(
    "crawler_app",
    broker=(
        f"pyamqp://{config.RABBITMQ_DEFAULT_USER}:{config.RABBITMQ_DEFAULT_PASS}@"
        f"{config.RABBITMQ_HOST}:{config.RABBITMQ_PORT}/"
    ),
    include=[
        "crawler.project_104.task_urls_104",
        "crawler.project_104.task_job_details_104",
        "crawler.project_104.task_category_104",
    ],
)

# --- [關鍵優化] 全局配置 ---
# 統一使用 JSON 序列化器，以獲得最佳的穩定性和相容性。
# 這可以解決許多潛在的 "任務無聲無息消失" 的問題。
app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # 保持 task_default_queue 的設定
    task_default_queue="worker_104",
    # 建議添加時區設定
    timezone="Asia/Taipei",
    enable_utc=True,
)