# crawler/api/main.py
"""
FastAPI 應用程式的主進入點。
定義所有 API 路由 (endpoints)。
"""
from fastapi import FastAPI, Depends, Query
from sqlmodel import Session, select
from typing import List
from datetime import date

from crawler.api.dependencies import get_db_session
from crawler.database.schema import Job  # 直接複用我們已有的 Job 模型


# 建立 FastAPI 應用實例
app = FastAPI(
    title="Crawler Job Data API",
    description="提供查詢已抓取的職缺數據的 API。",
    version="1.0.0",
)



# --- API 路由定義 ---

@app.get("/", tags=["General"])
def read_root():
    """根目錄，用於簡單的連線測試。"""
    return {"message": "Welcome to the Crawler Job Data API!"}


# 定義取得台灣股價的 API 路由
@app.get("/jobs/", response_model=List[Job], tags=["Jobs"])
def get_jobs(
    *,
    session: Session = Depends(get_db_session),
    company_name: str = Query(None, description="依公司名稱進行模糊查詢 (例如: '新加坡商')"),
    title: str = Query(None, description="依職稱進行模糊查詢 (例如: 'Python')"),
    limit: int = Query(10, description="回傳的資料筆數上限", ge=1, le=100)
) -> List[Job]:
    """
    查詢職缺資料。

    可以根據多種條件進行篩選和查詢。
    """
    # 使用 SQLModel 建立查詢語句，更安全、更優雅
    statement = select(Job)

    if company_name:
        statement = statement.where(Job.company_name.contains(company_name))
    
    if title:
        statement = statement.where(Job.title.contains(title))
    
    statement = statement.limit(limit)
    
    jobs = session.exec(statement).all()
    return jobs


# @app.get("/jobs")
# def taiwan_stock_price(
#     stock_id: str = "",  # 股票代號（可透過 URL query string 傳入）
#     start_date: str = "",  # 查詢起始日期（格式：YYYY-MM-DD）
#     end_date: str = "",  # 查詢結束日期（格式：YYYY-MM-DD）
# ):
#     # 根據參數組成 SQL 查詢語句
#     sql = f"""
#     select * from taiwan_stock_price
#     where StockID = '{stock_id}'
#     and Date>= '{start_date}'
#     and Date<= '{end_date}'
#     """
#     # 建立資料庫連線
#     mysql_conn = get_mysql_financialdata_conn()
#     # 使用 Pandas 執行 SQL 查詢並取得資料
#     data_df = pd.read_sql(sql, con=mysql_conn)
#     # 將資料轉為 List of Dict 格式，方便 FastAPI 回傳 JSON
#     data_dict = data_df.to_dict("records")
#     return {"data": data_dict}  # 回傳資料結果