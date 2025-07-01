# crawler/project_104/producer_urls.py
"""
職缺 URL Producer。

負責根據搜尋條件觸發 Celery 任務，以抓取職缺 URL 列表。
"""
import logging
from crawler.project_104 import config_104 as config
from crawler.project_104.task_urls_104 import fetch_and_save_all_urls

logger = logging.getLogger(__name__)


def run_producer_urls_main():
    """
    執行職缺 URL Producer 的主要邏輯：觸發一個 Celery 任務。
    """
    logger.info("觸發職缺 URL 抓取任務...")
    jobcat = config.JOBCAT_CODE
    keywords_list = config.KEYWORDS_LIST

    if not jobcat:
        logger.error("JOBCAT_CODE 未在 .env 中設定，無法執行 URL 抓取任務。")
        return

    if not keywords_list:
        logger.warning("KEYWORDS_LIST 未在 .env 中設定，將執行無關鍵字搜尋。")

    # 參數打包成 tuple (for args) 和 dict (for kwargs)
    task_args = (jobcat,)
    task_kwargs = {"keywords_list": keywords_list or [""]}

    try:
        # 優化：統一使用最直接的 apply_async，並明確指定隊列
        fetch_and_save_all_urls.apply_async(args=task_args, kwargs=task_kwargs, queue="worker_104")
        logger.info("職缺 URL 抓取任務已成功觸發。")
    except Exception as e:
        logger.error(f"觸發職缺 URL 抓取任務時發生錯誤: {e}", exc_info=True)


if __name__ == "__main__":
    from crawler.logging_config import setup_logging

    setup_logging()
    run_producer_urls_main()