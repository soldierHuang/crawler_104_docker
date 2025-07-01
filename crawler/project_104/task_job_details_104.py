# crawler/project_104/task_job_details_104.py
import logging
import pandas as pd
import requests
import time
import random
from typing import List, Any, Sequence, Dict, Optional
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from crawler.app import app
from crawler.database.repository import upsert_from_dataframe, get_all_urls_by_source
from crawler.project_104.constants_104 import HEADERS
from crawler.database.schema import Job

logger = logging.getLogger(__name__)

# --- 可調參數 ---
BATCH_SIZE = 100
MAX_WORKERS = 10 
REQUEST_TIMEOUT = 20
LOG_PROGRESS_INTERVAL = 100
# [新] 全局速率限制：每秒最多發起 N 個請求 (1/N = 每個請求的間隔)
# 例如，10 QPS (Query Per Second) -> 每個請求間隔 0.1 秒
REQUESTS_PER_SECOND = 10
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND

def _parse_api_data(api_data: Dict[str, Any], job_id: str) -> Job:
    """接收原始 API 資料，將其轉換並驗證為統一的 Job 模型。"""
    def safe_get(keys: Sequence[str], default: Any = None) -> Any:
        d = api_data
        for key in keys:
            if not isinstance(d, dict): return default
            d = d.get(key)
        return d if d is not None else default
    def extract_and_join(data_list: Optional[List[Dict]], key: str = 'description') -> Optional[str]:
        if not isinstance(data_list, list) or not data_list: return None
        items = [item.get(key, '').strip() for item in data_list if isinstance(item, dict) and item.get(key)]
        return ", ".join(filter(None, items)) or None
    def to_datetime_from_timestamp(v: Any) -> Optional[datetime]:
        if v and str(v).isdigit() and int(v) != 0:
            try: return datetime.fromtimestamp(int(v))
            except (ValueError, TypeError): return None
        return None
    def to_date_from_string(date_str: Optional[str]) -> Optional[date]:
        if not date_str: return None
        try: return datetime.strptime(date_str, "%Y/%m/%d").date()
        except ValueError: return None
    payload = {
        "job_id": job_id, "title": safe_get(['header', 'jobName']), "description": safe_get(['jobDetail', 'jobDescription']),
        "posted_date": to_date_from_string(safe_get(['header', 'appearDate'])), "salary": safe_get(['jobDetail', 'salary']),
        "salary_min": safe_get(['jobDetail', 'salaryMin']), "salary_max": safe_get(['jobDetail', 'salaryMax']),
        "salary_type": safe_get(['jobDetail', 'salaryType']), "work_time": safe_get(['jobDetail', 'workPeriod']),
        "work_type": safe_get(['jobDetail', 'jobType']), "need_employees": safe_get(['jobDetail', 'needEmp']),
        "location": safe_get(['jobDetail', 'addressRegion']), "company_address": safe_get(['jobDetail', 'addressDetail']),
        "longitude": safe_get(['jobDetail', 'longitude']), "latitude": safe_get(['jobDetail', 'latitude']),
        "degree": safe_get(['condition', 'edu']), "working_experience": safe_get(['condition', 'workExp']),
        "department": extract_and_join(safe_get(['condition', 'major'], [])), "qualification_required": extract_and_join(safe_get(['condition', 'specialty'], [])),
        "qualification_bonus": extract_and_join(safe_get(['condition', 'skill'], [])), "qualification_other": safe_get(['condition', 'other']),
        "company_id": safe_get(['custNo']), "company_name": safe_get(['header', 'custName']),
        "industry": safe_get(['industry']), "employees": safe_get(['employees']), "remote_work_type": safe_get(['jobDetail', 'remoteWork', 'type']),
        "remote_work_description": safe_get(['jobDetail', 'remoteWork', 'description']), "job_category": extract_and_join(safe_get(['jobDetail', 'jobCategory'], [])),
        "contact_person": safe_get(['contact', 'hrName']), "contact_phone": str(safe_get(['contact', 'phone'], [])),
        "last_processed_resume_at_time": to_datetime_from_timestamp(safe_get(['interactionRecord', 'lastProcessedResumeAtTime'])),
        "now_timestamp": to_datetime_from_timestamp(safe_get(['interactionRecord', 'nowTimestamp'])),
    }
    return Job(**payload)

@retry(
    retry=retry_if_exception_type(requests.HTTPError),
    stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=lambda rs: logger.warning(f"Request for {rs.args[0]} failed, retrying in {rs.next_action.sleep:.1f}s... (Attempt {rs.attempt_number})")
)
def _fetch_single_job_data(url: str) -> Optional[Job]:
    """抓取並解析單一職缺 URL，具備自動重試功能。"""
    try:
        job_id = url.split("/")[-1].split("?")[0]
        api_url = f"https://www.104.com.tw/job/ajax/content/{job_id}"
        response = requests.get(api_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        api_data = response.json().get("data")
        if not api_data: return None
        return _parse_api_data(api_data, job_id)
    except requests.RequestException:
        # 讓 tenacity 捕獲並重試
        raise
    except Exception as e:
        logger.exception(f"Non-retryable error on {url}")
        return None

def _flush_batch_to_db(job_batch: List[Dict]) -> None:
    """將一個批次的職缺資料寫入資料庫。"""
    if not job_batch: return
    logger.info(f"Flushing a batch of {len(job_batch)} jobs to database...")
    try:
        df_jobs = pd.DataFrame(job_batch)
        upsert_from_dataframe(df_jobs, "tb_jobs")
    except Exception:
        logger.exception("Batch database write failed")

@app.task(bind=True, name="crawler.project_104.task_job_details.fetch_and_save_all")
def fetch_and_save_all_job_details(self) -> str:
    """Celery 任務：獲取 URL，使用全局速率限制併發抓取，批次儲存。"""
    logger.info("Task started. Fetching URLs from database...")
    urls_to_process = list(get_all_urls_by_source(source="104"))
    total_urls = len(urls_to_process)

    if not total_urls:
        msg = "No URLs to process. Task finished."
        logger.info(msg)
        return msg

    logger.info(f"Fetched {total_urls} URLs. Starting processing with rate limit of {REQUESTS_PER_SECOND} QPS...")

    job_batch: List[Dict] = []
    total_processed = 0
    urls_completed = 0
    last_request_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # [關鍵優化] 引入速率限制
        futures = []
        for url in urls_to_process:
            # 確保距離上次請求已超過指定間隔
            time_since_last_request = time.time() - last_request_time
            if time_since_last_request < DELAY_BETWEEN_REQUESTS:
                time.sleep(DELAY_BETWEEN_REQUESTS - time_since_last_request)
            
            futures.append(executor.submit(_fetch_single_job_data, url))
            last_request_time = time.time()

        for future in as_completed(futures):
            urls_completed += 1
            try:
                job_model = future.result()
                if job_model:
                    job_batch.append(job_model.model_dump())
                    total_processed += 1
            except Exception as exc:
                # 重試後仍然失敗的異常會在這裡被捕獲
                logger.error(f"A sub-task failed permanently: {exc}")

            if len(job_batch) >= BATCH_SIZE:
                _flush_batch_to_db(job_batch)
                job_batch.clear()

            if urls_completed % LOG_PROGRESS_INTERVAL == 0:
                logger.info(f"Progress: {urls_completed}/{total_urls} URLs attempted.")

    if job_batch:
        _flush_batch_to_db(job_batch)

    summary = f"Task finished. Attempted {total_urls} URLs, successfully parsed {total_processed} jobs."
    logger.info(summary)
    return summary