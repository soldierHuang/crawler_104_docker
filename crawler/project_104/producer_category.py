# crawler/project_104/producer_category.py
"""
職位類別 Producer。

負責觸發 Celery 任務，以抓取並處理職位類別資料。
"""
import logging
from crawler.project_104.task_category_104 import process_category_data

logger = logging.getLogger(__name__)


def run_producer_category_main():
    """
    執行職位類別 Producer 的主要邏輯：觸發一個 Celery 任務。
    """
    logger.info("觸發職位類別資料處理任務...")
    try:
        # 優化：統一使用最直接的 apply_async，並明確指定隊列
        process_category_data.apply_async(queue="worker_104")
        logger.info("職位類別資料處理任務已成功觸發。")
    except Exception as e:
        logger.error(f"觸發職位類別資料處理任務時發生錯誤: {e}", exc_info=True)


if __name__ == "__main__":
    from crawler.logging_config import setup_logging

    setup_logging()
    run_producer_category_main()