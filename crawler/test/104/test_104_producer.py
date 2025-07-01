# crawler/test/104/test_104_producer.py
"""
針對 project_104 Producer 的功能進行測試。
"""

from unittest.mock import patch, call, ANY, MagicMock

from crawler.project_104.producer_urls import run_producer_urls_main
from crawler.project_104.producer_job_details import run_producer_job_details_main
from crawler.project_104.task_page_scraper import process_single_page_scraping
from crawler.project_104.task_104 import process_single_job_data
from crawler.database_operations import save_job_urls_to_db, get_urls_from_db


@patch("crawler.project_104.task_page_scraper.process_single_page_scraping")
@patch("crawler.database_operations.save_job_urls_to_db")
def test_producer_urls_main_normal_case(
    mock_save_job_urls_to_db, mock_process_single_page_scraping
):
    """測試 producer_urls.py 在正常情況下，是否能正確執行並儲存 URL。"""
    # --- Mocking ---
    # 模擬 process_single_page_scraping.delay().get() 的行為
    mock_async_result = MagicMock()
    mock_async_result.get.side_effect = [
        {"page": 1, "urls": {"url_1_1", "url_1_2"}, "max_pages": 5},
        {"page": 2, "urls": {"url_2_1", "url_2_2"}, "max_pages": 5},
        {"page": 3, "urls": {"url_3_1", "url_3_2"}, "max_pages": 5},
        {"page": 4, "urls": {"url_4_1", "url_4_2"}, "max_pages": 5},
        {"page": 5, "urls": {"url_5_1", "url_5_2"}, "max_pages": 5},
    ]
    mock_process_single_page_scraping.delay.return_value = mock_async_result

    # --- Execution ---
    run_producer_urls_main()

    # --- Assertion ---
    # 檢查 process_single_page_scraping.delay 是否被正確呼叫
    assert (
        mock_process_single_page_scraping.delay.call_count == 5
    )  # 1 (first page) + 4 (remaining pages)
    mock_process_single_page_scraping.delay.assert_has_calls(
        [
            call(1, ANY),
            call(2, ANY),
            call(3, ANY),
            call(4, ANY),
            call(5, ANY),
        ],
        any_order=True,
    )

    # 檢查 save_job_urls_to_db 是否被正確呼叫
    mock_save_job_urls_to_db.assert_called_once()
    saved_urls = mock_save_job_urls_to_db.call_args[0][0]
    assert len(saved_urls) == 10  # 5 pages * 2 urls/page
    assert "url_1_1" in saved_urls
    assert "url_5_2" in saved_urls


@patch("crawler.project_104.task_page_scraper.process_single_page_scraping")
@patch("crawler.database_operations.save_job_urls_to_db")
def test_producer_urls_main_empty_case(
    mock_save_job_urls_to_db, mock_process_single_page_scraping
):
    """測試 producer_urls.py 當沒有 URL 時，是否能優雅地處理。"""
    # --- Mocking ---
    # 模擬 process_single_page_scraping.delay().get() 返回空 URL 列表
    mock_async_result = MagicMock()
    mock_async_result.get.return_value = {"page": 1, "urls": set(), "max_pages": 1}
    mock_process_single_page_scraping.delay.return_value = mock_async_result

    # --- Execution ---
    run_producer_urls_main()

    # --- Assertion ---
    # 檢查 process_single_page_scraping.delay 是否只被呼叫一次 (第一頁)
    mock_process_single_page_scraping.delay.assert_called_once_with(1, ANY)

    # 檢查 save_job_urls_to_db 是否被呼叫，但傳入空的 URL 集合
    mock_save_job_urls_to_db.assert_called_once_with(set(), source="104")


@patch("crawler.database_operations.get_urls_from_db")
@patch("crawler.project_104.task_104.process_single_job_data")
def test_producer_job_details_main(mock_process_single_job_data, mock_get_urls_from_db):
    """測試 producer_job_details.py 是否能正確從資料庫獲取 URL 並分派任務。"""
    # --- Mocking ---
    test_urls = {"https://www.104.com.tw/job/a", "https://www.104.com.tw/job/b"}
    mock_get_urls_from_db.return_value = test_urls

    # --- Execution ---
    run_producer_job_details_main()

    # --- Assertion ---
    mock_get_urls_from_db.assert_called_once_with(limit=None)
    assert mock_process_single_job_data.apply_async.call_count == 2
    mock_process_single_job_data.apply_async.assert_has_calls(
        [
            call(("https://www.104.com.tw/job/ajax/content/a",), queue="worker_104"),
            call(("https://www.104.com.tw/job/ajax/content/b",), queue="worker_104"),
        ],
        any_order=True,
    )
