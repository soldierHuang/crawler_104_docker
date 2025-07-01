# crawler/project_104/constants_104.py
"""
定義 104 人力銀行爬蟲專案中使用的全域常數。

此檔案用於存放「程式碼內在的、不應隨環境或使用者意圖變化的」固定值。
這些值是程式邏輯的一部分，應被納入版本控制。

與 `local.ini` 的區別：
- `constants.py`: 存放程式的「本質」，如身份標識 (HEADERS)。
- `local.ini`: 存放程式的「行為參數」，如搜尋關鍵字、並行數量等，用於外部配置。
"""

from typing import Dict

WEB_NAME: str = "104_人力銀行"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Referer": "https://www.104.com.tw/jobs/search",
}
