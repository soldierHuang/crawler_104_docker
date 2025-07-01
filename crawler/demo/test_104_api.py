import requests

url = "https://www.104.com.tw/job/ajax/content/22fct"
headers_1 = {
    "referer": "https://www.104.com.tw/job/22fct",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
}

response = requests.get(url, headers=headers_1)
data = response.json()

print(data)


# headers_2 = {
#     "referer": "https://www.104.com.tw/job/ajax/content/22fct",
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
# }


#    * 原始 URL: https://www.104.com.tw/job/22fct
#    * 構造的 API URL: https://www.104.com.tw/job/ajax/content/22fct
