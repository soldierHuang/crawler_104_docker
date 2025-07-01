# crawler/api/dependencies.py
"""
定義 FastAPI 應用中使用的依賴項。
"""
from typing import Generator
from sqlmodel import Session
from crawler.database.connection import get_engine

def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI 依賴項：為每個請求提供一個資料庫 Session。

    使用 `yield` 確保 session 在請求處理完畢後總能被關閉，
    即使在處理過程中發生了錯誤。
    """
    engine = get_engine()
    with Session(engine) as session:
        yield session