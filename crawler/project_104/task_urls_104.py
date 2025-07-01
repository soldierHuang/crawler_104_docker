# crawler/project_104/task_urls_104.py
import logging
import time
import random
import requests
import pandas as pd
from datetime import datetime
from typing import Set, List, Optional, Callable, Iterable, Generator, ClassVar
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from crawler.app import app

# 更改導入路徑，使用新的 repository
from crawler.database.repository import upsert_from_dataframe
from crawler.project_104 import config_104 as config

logger = logging.getLogger(__name__)

# ... (KeywordScraper 和 run_concurrently 內容不變)
# ==============================================================================
# 1. 通用工具層 (Utility Layer) - 最底層的基礎
# ==============================================================================


def run_concurrently(
    tasks: Iterable, task_function: Callable, max_workers: int
) -> Generator:
    """通用的併發執行器，被上層邏輯呼叫。"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {executor.submit(task_function, task): task for task in tasks}
        for future in as_completed(future_to_task):
            try:
                yield future.result()
            except Exception as exc:
                task = future_to_task[future]
                logger.error(f"執行任務 '{task}' 時發生錯誤: {exc}", exc_info=False)


# ==============================================================================
# 2. 核心抓取單元 (Core Scraping Unit) - 構建在工具之上
# ==============================================================================


@dataclass(frozen=True)
class KeywordScraper:
    """一個使用 dataclass 的、完全自洽的爬蟲物件。"""

    keyword: str
    jobcat_code: str
    order: int
    max_pages_limit: int

    BASE_URL: ClassVar[str] = "https://www.104.com.tw/jobs/search/"
    BASE_PARAMS: ClassVar[dict] = {"jobsource": "index_s", "mode": "s"}

    def scrape(self) -> Set[str]:
        first_page_soup = self._fetch_soup(1)
        if not first_page_soup:
            return set()

        all_urls = self._parse_job_urls(first_page_soup)
        has_urls_on_first_page = bool(all_urls)

        effective_max = min(
            self.max_pages_limit,
            self._parse_max_pages(first_page_soup, has_urls_on_first_page),
        )
        logger.info(f"開始抓取: {self}, 有效頁數: {effective_max}")

        if effective_max > 1:
            remaining_pages = range(2, effective_max + 1)
            # Assuming config has MAX_WORKERS_PER_KEYWORD, otherwise use a default
            max_workers = getattr(config, "MAX_WORKERS_PER_KEYWORD", 5)
            soups = run_concurrently(remaining_pages, self._fetch_soup, max_workers)
            all_urls.update(set.union(*(self._parse_job_urls(s) for s in soups if s)))

        return all_urls

    def _fetch_soup(self, page: int) -> Optional[BeautifulSoup]:
        params = {
            **self.BASE_PARAMS,
            "jobcat": self.jobcat_code,
            "keyword": self.keyword,
            "order": self.order,
            "page": page,
        }
        try:
            time.sleep(random.uniform(0.1, 0.5))
            response = requests.get(self.BASE_URL, params=params, timeout=20)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            logger.error(f"抓取失敗: {self} on page {page} - {e}")
            return None

    @staticmethod
    def _parse_job_urls(soup: BeautifulSoup) -> Set[str]:
        urls = set()
        job_articles = soup.find_all("div", class_="job-summary")
        for article in job_articles:
            a_tag = article.find("a", class_="info-job__text")
            if a_tag and a_tag.get("href"):
                # 確保 URL 格式正確
                full_url = urljoin("https:", a_tag["href"])
                # 清理 URL 參數
                clean_url = urlparse(full_url)._replace(query="").geturl()
                urls.add(clean_url)
        return urls

    @staticmethod
    def _parse_max_pages(soup: BeautifulSoup, has_urls: bool) -> int:
        page_buttons = soup.select("a.paging__link")
        if not page_buttons:
            return 1 if has_urls else 0
        page_numbers = [int(btn.text) for btn in page_buttons if btn.text.isdigit()]
        return max(page_numbers) if page_numbers else (1 if has_urls else 0)


def _save_job_urls_to_db(job_urls: Set[str], source: str = "104"):
    if not job_urls:
        logger.info("沒有新的職缺 URL 需要儲存。")
        return
    current_time = datetime.now()
    df = pd.DataFrame(
        [
            {
                "source_url": url,
                "source": source,
                "crawled_at": current_time,
                "updated_at": current_time,
            }
            for url in job_urls
        ]
    )
    try:
        # 使用新的 repository 函數
        upsert_from_dataframe(df, "tb_urls")
        logger.info(f"成功儲存 {len(df)} 個職缺 URL。")
    except Exception as e:
        logger.error(f"儲存 URL 到資料庫失敗: {e}", exc_info=True)
        raise


# ... (_run_scraping_session 和 fetch_and_save_all_urls 內容不變，但內部呼叫已更新)
def _run_scraping_session(keywords: List[str], jobcat_code: str) -> Set[str]:
    """協調多個關鍵字的抓取任務。"""
    max_workers = getattr(config, "MAX_WORKERS", 10)
    scrapers = (
        KeywordScraper(kw, jobcat_code, config.ORDER_SETTING, config.MAX_PAGES)
        for kw in keywords
    )
    url_sets_generator = run_concurrently(scrapers, lambda s: s.scrape(), max_workers)
    return set().union(*(url_set for url_set in url_sets_generator if url_set))


@app.task(bind=True)
def fetch_and_save_all_urls(
    self, jobcat_code: str, keywords_list: Optional[List[str]] = None
):
    """Celery 任務，整個流程的最高層協調者。"""
    task_id = self.request.id
    logger.info(
        f"[Task: {task_id}] 任務啟動。職務: {jobcat_code}, 關鍵字: {keywords_list}"
    )

    if not jobcat_code:
        logger.error(f"[Task: {task_id}] 缺少職務代碼，任務終止。")
        return

    keywords = keywords_list or [""]

    all_job_urls = _run_scraping_session(keywords, jobcat_code)

    logger.info(
        f"[Task: {task_id}] 抓取完成，共發現 {len(all_job_urls)} 個不重複 URL。"
    )

    if all_job_urls:
        _save_job_urls_to_db(all_job_urls)
    else:
        logger.warning(f"[Task: {task_id}] 本次任務未抓取到任何 URL。")

    logger.info(f"[Task: {task_id}] 任務執行完畢。")
