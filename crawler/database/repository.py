# crawler/database/repository.py
"""
資料存取層 (Data Access Layer) / Repository 模式。

此模組封裝了所有與資料庫的互動邏輯 (CRUD 操作)。
應用程式的其他部分 (例如 Celery tasks) 應該透過此模組來存取資料，
而不是直接操作 Engine 或 Connection。
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Set, Optional

from sqlalchemy.dialects.mysql import insert
from sqlmodel import select

from crawler.database.connection import get_engine
from crawler.database.schema import metadata, Url

logger = logging.getLogger(__name__)


def _sanitize_dataframe_for_mysql(df: pd.DataFrame) -> pd.DataFrame:
    """
    一個健壯的函數，用於清理 DataFrame 以便能安全地寫入 MySQL。

    它會將所有 np.nan 和 pd.NA 替換為 None，這是 SQLAlchemy 能正確處理為 NULL 的值。

    Args:
        df (pd.DataFrame): 原始的 DataFrame。

    Returns:
        pd.DataFrame: 清理過的 DataFrame 副本。
    """
    # where() 函數比 fillna() 或 replace() 更為可靠和通用。
    return df.replace({np.nan: None, pd.NA: None})


def upsert_from_dataframe(df: pd.DataFrame, table_name: str) -> None:
    """
    將 Pandas DataFrame 的資料執行 "Upsert" 操作到指定的資料庫表格。

    此函數包含一個預處理步驟，以確保沒有 NaN 值傳遞給資料庫，並能處理
    主鍵衝突的情況（更新現有記錄）。

    Args:
        df (pd.DataFrame): 要寫入的 DataFrame。
        table_name (str): 目標資料表名稱。
    """
    if df.empty:
        logger.info(f"傳入的 DataFrame 為空，無需對表格 '{table_name}' 執行操作。")
        return

    logger.debug(f"開始淨化表格 '{table_name}' 的 DataFrame...")
    df_sanitized = _sanitize_dataframe_for_mysql(df)
    logger.debug("DataFrame 淨化完成。")
    
    engine = get_engine()

    try:
        target_table = metadata.tables[table_name]
        primary_key_cols = {col.name for col in target_table.primary_key.columns}
        if not primary_key_cols:
            raise ValueError(
                f"表格 '{table_name}' 沒有定義主鍵，無法執行 upsert 操作。"
            )

        data_to_insert = df_sanitized.to_dict(orient="records")

        with engine.begin() as connection:
            stmt = insert(target_table).values(data_to_insert)

            update_cols = {
                col.name: stmt.inserted[col.name]
                for col in target_table.columns
                if col.name not in primary_key_cols
            }

            if update_cols:
                final_stmt = stmt.on_duplicate_key_update(**update_cols)
            else:
                # 如果沒有非主鍵欄位，則退化為普通的 INSERT IGNORE
                final_stmt = stmt.prefix_with("INSERT IGNORE")

            result = connection.execute(final_stmt)
            logger.info(
                f"成功將 {result.rowcount} 筆資料 Upsert 到表格: {table_name}"
            )

    except KeyError:
        logger.error(f"表格 '{table_name}' 不存在於定義的 schema 中。")
        raise
    except Exception as e:
        logger.error(f"執行 Upsert 到 {table_name} 時發生錯誤: {e}", exc_info=True)
        raise


def get_all_urls_by_source(source: str) -> Set[str]:
    """
    從 tb_urls 資料表中獲取指定來源的所有 URL。

    Args:
        source (str): 篩選特定來源的 URL，例如 "104"。

    Returns:
        Set[str]: 包含不重複 URL 的集合。
    """
    engine = get_engine()
    urls: Set[str] = set()
    try:
        with engine.connect() as connection:
            query = select(Url.source_url).where(Url.source == source)
            result = connection.execute(query)
            # 優化：使用 .scalars().all() 直接獲取第一欄的純量值列表，可讀性更高。
            urls = set(result.scalars().all())
        logger.info(f"從 tb_urls 資料表為來源 '{source}' 獲取了 {len(urls)} 筆 URL。")
    except Exception as e:
        logger.error(f"從 tb_urls 資料表獲取 URL 時發生錯誤: {e}", exc_info=True)
        # 發生錯誤時返回空集合，避免後續邏輯出錯
        return set()
    return urls