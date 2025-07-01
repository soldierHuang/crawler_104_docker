# crawler/database/connection.py
"""
此模組負責管理應用程式的資料庫連線。

它使用模組級別的單例模式創建一個全域的 SQLAlchemy Engine，
確保在整個應用程式生命週期中只有一個連線池。
同時，提供初始化資料庫表格的函數。
"""

import logging
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from tenacity import retry, stop_after_attempt, wait_fixed, before_log, RetryError

from crawler import config
from crawler.database.schema import metadata  # 從統一的 schema 位置導入 metadata

logger = logging.getLogger(__name__)

# --- 優化：模組級別的單例實現 ---
# Python 模組的導入機制保證了這段程式碼只會執行一次，
# 這是實現單例最簡單、最安全的方式。

def _create_and_connect_engine() -> Engine:
    """
    內部函數，負責創建並測試 Engine 連線。
    帶有重試機制，以應對資料庫服務尚未就緒的情況。
    """
    try:
        @retry(
            stop=stop_after_attempt(5),
            wait=wait_fixed(3),
            before=before_log(logger, logging.INFO),
            reraise=True  # 確保重試失敗後拋出原始異常
        )
        def _connect_with_retry() -> Engine:
            logger.info("正在嘗試建立 MySQL 引擎...")
            address = (
                f"mysql+pymysql://{config.MYSQL_ACCOUNT}:{config.MYSQL_PASSWORD}@"
                f"{config.MYSQL_HOST}:{config.MYSQL_PORT}/{config.MYSQL_DATABASE}"
                f"?charset=utf8mb4" # 確保使用 utf8mb4
            )
            engine = create_engine(address, pool_recycle=3600, echo=False) # 生產環境建議 echo=False

            # 建立連線測試，如果失敗則觸發重試
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            
            logger.info("MySQL 引擎已成功建立並通過連線測試。")
            return engine

        return _connect_with_retry()

    except (OperationalError, RetryError) as e:
        logger.critical(f"無法在重試後連線到 MySQL，應用程式可能無法啟動。錯誤: {e}")
        # 在無法建立資料庫連線時，直接拋出異常讓應用程式啟動失敗，
        # 這通常比讓它在"損壞"狀態下運行更安全。
        raise
    except Exception as e:
        logger.critical(f"創建 MySQL 引擎時發生未預期的嚴重錯誤: {e}", exc_info=True)
        raise

# 在模組加載時直接初始化 Engine
_engine: Engine = _create_and_connect_engine()


def get_engine() -> Engine:
    """
    獲取全域唯一的 SQLAlchemy Engine 單例。
    """
    return _engine


def initialize_database_tables() -> None:
    """
    確保所有在 metadata 中定義的資料表都存在於資料庫中。
    此函數應在應用程式啟動時呼叫一次。
    """
    logger.info("正在檢查並初始化資料庫表格...")
    try:
        engine = get_engine()
        # create_all 會聰明地檢查每個表格是否存在，不存在才會建立
        metadata.create_all(engine) # checkfirst=True 是預設行為，可以省略
        logger.info("資料庫表格初始化檢查完成。")
    except Exception as e:
        logger.critical(
            f"資料庫表格初始化失敗，應用程式可能無法正常運作。錯誤: {e}", exc_info=True
        )
        raise