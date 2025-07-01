# crawler/database/schema.py
"""
定義應用程式中使用的所有資料庫表格結構。
"""
from datetime import datetime, date
from typing import Optional

from sqlmodel import Field, SQLModel, Column, Text, TIMESTAMP, DATE

class Job(SQLModel, table=True):
    """代表單一職缺的資料模型"""
    __tablename__ = "tb_jobs"

    job_id: str = Field(primary_key=True, max_length=50)
    title: str = Field(max_length=255)
    description: str = Field(sa_column=Column(Text))
    posted_date: Optional[date] = Field(default=None, sa_column=Column(DATE))
    
    salary: str = Field(max_length=255)
    salary_min: Optional[int] = Field(default=None)
    salary_max: Optional[int] = Field(default=None)
    salary_type: Optional[int] = Field(default=None)

    work_time: str = Field(max_length=100)
    work_type: Optional[int] = Field(default=None)
    need_employees: Optional[str] = Field(default=None, max_length=50)
    
    location: str = Field(max_length=100)
    company_address: str = Field(max_length=255)
    longitude: Optional[str] = Field(default=None, max_length=50)
    latitude: Optional[str] = Field(default=None, max_length=50)
    
    degree: str = Field(max_length=100)
    working_experience: str = Field(max_length=100)
    department: Optional[str] = Field(default=None, sa_column=Column(Text))
    qualification_required: Optional[str] = Field(default=None, sa_column=Column(Text))
    qualification_bonus: Optional[str] = Field(default=None, sa_column=Column(Text))
    qualification_other: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    company_id: str = Field(max_length=50)
    company_name: str = Field(max_length=255)
    industry: Optional[str] = Field(default=None, max_length=255)
    employees: Optional[str] = Field(default=None, max_length=255)

    remote_work_type: Optional[str] = Field(default=None, max_length=50)
    remote_work_description: Optional[str] = Field(default=None, sa_column=Column(Text))

    job_category: Optional[str] = Field(default=None, sa_column=Column(Text))
    contact_person: Optional[str] = Field(default=None, max_length=100)
    contact_phone: Optional[str] = Field(default=None, max_length=255)
    last_processed_resume_at_time: Optional[datetime] = Field(default=None)
    now_timestamp: Optional[datetime] = Field(default=None)
    update_date: date = Field(default_factory=date.today)

class Url(SQLModel, table=True):
    __tablename__ = "tb_urls"
    source_url: str = Field(primary_key=True, max_length=255)
    source: str = Field(max_length=50)
    crawled_at: datetime = Field(sa_column=Column(TIMESTAMP))
    updated_at: datetime = Field(sa_column=Column(TIMESTAMP))
    status: str = Field(default="new", max_length=20)

class Category(SQLModel, table=True):
    __tablename__ = "tb_category"
    category_id: str = Field(primary_key=True, max_length=50)
    category_name: str = Field(max_length=255)
    parent_code: str = Field(max_length=50)
    parent_name: str = Field(max_length=255)
    source: str = Field(max_length=50)
    created_at: datetime = Field(sa_column=Column(TIMESTAMP))
    updated_at: datetime = Field(sa_column=Column(TIMESTAMP))

metadata = SQLModel.metadata