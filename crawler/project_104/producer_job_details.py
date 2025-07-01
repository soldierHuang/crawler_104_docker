# crawler/project_104/producer_job_details.py
"""
職缺詳細資料 Producer (最終優雅版)。

通過探測 Worker 是否在線來決定是否觸發任務，
確保任務只在系統準備就緒時發送，且避免了複雜的狀態檢查。
"""
import logging
import time
from typing import Optional, List, Dict

from crawler.app import app
from crawler.project_104.task_job_details_104 import (
    fetch_and_save_all_job_details,
)

logger = logging.getLogger(__name__)


def is_worker_online(timeout: int = 5) -> bool:
    """
    通過 ping 命令探測是否有任何 Celery worker 在線。

    Args:
        timeout (int): 等待回應的秒數。

    Returns:
        bool: 如果至少有一個 worker 回應，則返回 True。
    """
    # inspector.ping() 會向所有 worker 發送 ping 命令
    # 它返回一個字典，鍵是 worker 名稱，值是 {'ok': 'pong'}
    responses: Optional[Dict[str, Dict]] = app.control.inspect(timeout=timeout).ping()
    
    # 如果 responses 不是 None 且不為空，說明至少有一個 worker 回應了
    return bool(responses)


def run_producer_job_details_main() -> None:
    """
    執行職缺詳細資料 Producer 的主要邏輯：
    1. 探測 Worker 是否在線。
    2. 如果在線，則觸發一個新的 Celery 任務。
    """
    logger.info("準備觸發職缺詳細資料抓取任務...")

    if not is_worker_online():
        logger.error(
            "探測不到任何在線的 Celery Worker。請先啟動 Worker 服務。任務未觸發。"
        )
        return

    try:
        # 系統在線，放心發送任務
        fetch_and_save_all_job_details.apply_async(queue="worker_104")
        logger.info(
            f"已成功觸發任務 '{fetch_and_save_all_job_details.name}'。"
        )

    except Exception as e:
        logger.error(f"觸發任務時發生 broker 連線錯誤: {e}", exc_info=True)


if __name__ == "__main__":
    from crawler.logging_config import setup_logging
    setup_logging()
    
    run_producer_job_details_main()