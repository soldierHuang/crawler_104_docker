# crawler/project_104/config_104.py
"""
此模組包含 104 人力銀行爬蟲專案特有的配置設定。
"""

import os
from dotenv import load_dotenv
from typing import List, Optional

# Load .env once when this module is imported
load_dotenv()

# 104 Crawler Specific Settings
JOBCAT_CODE: Optional[str] = os.environ.get("JOBCAT_CODE")
KEYWORDS_STR: str = os.environ.get("KEYWORDS", "")
KEYWORDS_LIST: List[str] = [kw.strip() for kw in KEYWORDS_STR.split(",") if kw.strip()]
MAX_PAGES: int = int(os.environ.get("MAX_PAGES", "100"))
ORDER_SETTING: int = int(os.environ.get("ORDER_SETTING", "15"))
RETRY_COUNT: int = int(os.environ.get("RETRY_COUNT", "3"))
RETRY_DELAY_SECONDS: int = int(os.environ.get("RETRY_DELAY_SECONDS", "5"))
MAX_WORKERS: int = int(os.environ.get("MAX_WORKERS", "10"))
BATCH_SIZE: int = int(os.environ.get("BATCH_SIZE", "10"))
