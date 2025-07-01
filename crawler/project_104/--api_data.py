import pandas as pd
import requests

web_url = "https://www.104.com.tw/job/7rnfh?jobsource=index_s"

job_id = web_url.split("/")[-1].split("?")[0]
api_url = f"https://www.104.com.tw/job/ajax/content/{job_id}"


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Referer": api_url,
}


response = requests.get(api_url, headers=HEADERS, timeout=20)
response.raise_for_status()

api_data = response.json().get("data")
print(api_data)