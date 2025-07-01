# crawler/project_104/task_category_104.py
import logging
import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from crawler.app import app
from crawler.project_104.constants_104 import HEADERS
from crawler.database.repository import upsert_from_dataframe
from crawler.utilis.data_processing import flatten_jobcat_recursive

logger = logging.getLogger(__name__)

# --- 定義一個專用的資料目錄，這個路徑只在容器內部有效 ---
# 這樣可以避免 Docker volume mount 帶來的權限問題
CONTAINER_DATA_DIR = "/home/app_user/data"

@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="crawler.project_104.task_category_104.process_category_data",
)
def process_category_data(self, cache_duration_hours: int = 720) -> None:
    """
    一個 Celery 任務，用於抓取、處理和儲存 104 人力銀行的所有職位類別。
    此任務包含本地快取機制，以避免頻繁請求 API。
    """
    logger.info("開始處理職位類別資料...")

    # 優化：使用絕對路徑指向容器內專用的資料目錄
    data_dir = CONTAINER_DATA_DIR
    os.makedirs(data_dir, exist_ok=True) # 確保目錄存在

    file_jobcat_csv: str = os.path.join(data_dir, "104_人力銀行_category.csv")
    url_JobCat: str = "https://static.104.com.tw/category-tool/json/JobCat.json"

    df_jobcat_sorted: Optional[pd.DataFrame] = None

    if os.path.exists(file_jobcat_csv):
        modified_time = datetime.fromtimestamp(os.path.getmtime(file_jobcat_csv))
        if datetime.now() - modified_time < timedelta(hours=cache_duration_hours):
            logger.info(f"從有效快取中載入職業總覽資料: {file_jobcat_csv}")
            try:
                df_jobcat_sorted = pd.read_csv(file_jobcat_csv)
            except Exception as e:
                logger.warning(f"讀取快取檔案失敗: {e}, 將嘗試從網路重新獲取。")
                df_jobcat_sorted = None

    if df_jobcat_sorted is None:
        try:
            logger.info(f"本地快取無效或不存在，從網路獲取職業總覽資料: {url_JobCat}")
            response_jobcat: requests.Response = requests.get(
                url_JobCat, headers=HEADERS, timeout=10
            )
            response_jobcat.raise_for_status()
            jobcat_data: Dict[str, Any] = response_jobcat.json()

            flattened_data: List[Dict[str, str]] = flatten_jobcat_recursive(jobcat_data)
            df_jobcat: pd.DataFrame = pd.DataFrame(flattened_data)
            df_jobcat_sorted: pd.DataFrame = df_jobcat.sort_values(by="job_code")
            df_jobcat_sorted = df_jobcat_sorted.rename(
                columns={"job_code": "category_id", "job_name": "category_name"}
            )
            # 現在會寫入到 /home/app_user/data/104_人力銀行_category.csv
            df_jobcat_sorted.to_csv(file_jobcat_csv, index=False, encoding="utf-8-sig")
            logger.info(f"職業總覽資料已成功抓取並儲存為 CSV 快取: '{file_jobcat_csv}'")
        except requests.RequestException as exc:
            logger.error(f"從網路獲取職位類別資料失敗: {exc}")
            if os.path.exists(file_jobcat_csv):
                logger.warning(f"網路獲取失敗，將使用過期的快取檔案: {file_jobcat_csv}")
                try:
                    df_jobcat_sorted = pd.read_csv(file_jobcat_csv)
                except Exception as e:
                    logger.error(f"讀取過期快取檔案也失敗了: {e}, 任務重試。")
                    raise self.retry(exc=exc)
            else:
                logger.error("網路獲取失敗且無任何快取可用，任務重試。")
                raise self.retry(exc=exc)

    if df_jobcat_sorted is not None and not df_jobcat_sorted.empty:
        try:
            df_jobcat_sorted["source"] = "104"
            now = datetime.now()
            df_jobcat_sorted["created_at"] = now
            df_jobcat_sorted["updated_at"] = now
            
            upsert_from_dataframe(df_jobcat_sorted, "tb_category")
            
            logger.info("職業總覽資料已成功同步到資料庫。")
        except Exception as e:
            logger.error(f"儲存職位類別資料到資料庫時失敗: {e}", exc_info=True)

    logger.info("職位類別資料處理完成。")


def run_category_main() -> None:
    """
    本地執行的主函數，用於觸發 Celery 任務。
    主要用於開發和調試。
    """
    logger.info("觸發職位類別資料處理任務...")
    process_category_data.delay()
    logger.info("職位類別資料處理任務已成功觸發。")


if __name__ == "__main__":
    from crawler.logging_config import setup_logging

    setup_logging()
    run_category_main()