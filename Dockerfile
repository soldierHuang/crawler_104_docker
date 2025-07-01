# ---- 建置階段 (Builder Stage) ----
FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

COPY requirements.txt .

RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --no-cache-dir -r requirements.txt


# ---- 最終階段 (Final Stage) ----
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# ---- [優化] 以 root 身份完成所有系統級操作 ----
# 1. 建立 app_user
RUN useradd --system --shell /bin/bash app_user

# 2. 創建應用程式需要的目錄
#    - /home/app_user/app: 用於存放程式碼
#    - /home/app_user/data: 用於存放快取等持久化資料
RUN mkdir -p /home/app_user/app /home/app_user/data

# 3. 將這些目錄的所有權一次性交給 app_user
RUN chown -R app_user:app_user /home/app_user

# 從建置階段複製虛擬環境
# 注意：由於後續會切換用戶，這裡先不指定 chown，或者直接複製到一個臨時位置
COPY --from=builder /opt/venv /opt/venv

# ---- [關鍵] 在所有系統操作完成後，切換到非 root 用戶 ----
USER app_user

# 切換工作目錄
WORKDIR /home/app_user/app

# 複製應用程式碼 (這會被 docker-compose 的 volume mount 覆蓋，用於開發)
# 由於當前用戶已是 app_user，無需再指定 chown
COPY . .

# 設定環境變數
ENV PATH="/opt/venv/bin:$PATH"