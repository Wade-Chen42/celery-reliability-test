FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    redis-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY src/ ./src/
COPY tests/ ./tests/
COPY scripts/ ./scripts/

# 設定 Python 路徑
ENV PYTHONPATH=/app:$PYTHONPATH

# 建立結果目錄
RUN mkdir -p /app/results

# 預設命令
CMD ["celery", "-A", "src.celery_app", "worker", "--loglevel=info"]