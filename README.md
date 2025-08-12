# Celery Reliability Test Project

獨立的 Celery 可靠性測試專案，用於驗證 Celery + Redis 的可靠性機制。

## 為什麼需要獨立測試環境？

1. **隔離性**：避免影響主專案的 Redis 資料
2. **可控性**：可以隨意重啟、清空 Redis
3. **實驗性**：可以測試極端情況（如強制 kill worker）
4. **配置彈性**：使用不同的 Redis 配置進行測試

## 專案結構

```
celery-reliability-test/
├── README.md                 # 本文檔
├── docker-compose.yml        # Docker 環境配置
├── Makefile                 # 快捷指令
├── requirements.txt         # Python 依賴
├── .env.example            # 環境變數範例
├── redis/
│   ├── redis.conf          # Redis 配置
│   └── data/              # Redis 資料目錄
├── src/
│   ├── celery_app.py      # Celery 應用配置
│   ├── tasks.py           # 測試任務
│   └── utils.py           # 工具函數
├── tests/
│   ├── test_persistence.py    # 持久化測試
│   ├── test_retry.py         # 重試機制測試
│   ├── test_recovery.py      # 恢復機制測試
│   └── test_pipeline.py      # Pipeline 測試
├── scripts/
│   ├── run_tests.sh          # 執行所有測試
│   ├── simulate_crash.sh     # 模擬崩潰
│   └── monitor.sh            # 監控腳本
└── results/
    └── test_report.md        # 測試報告
```

## 快速開始

### 1. 環境準備

```bash
# Clone 專案
cd /Users/moraleai_ml_engineer
git clone [your-repo] celery-reliability-test
cd celery-reliability-test

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # MacOS/Linux
# or
venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt
```

### 2. 使用 Docker Compose

```bash
# 啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

### 3. 執行測試

```bash
# 執行所有測試
make test-all

# 執行特定測試
make test-persistence
make test-retry
make test-recovery

# 生成報告
make report
```

## 測試場景

### 場景 1：Redis 崩潰測試
```bash
# 啟動測試
make test-redis-crash

# 這會：
# 1. 發送 100 個任務
# 2. 強制停止 Redis
# 3. 重啟 Redis
# 4. 檢查任務恢復情況
```

### 場景 2：Worker 崩潰測試
```bash
# 啟動測試
make test-worker-crash

# 這會：
# 1. 啟動長時間任務
# 2. 強制 kill worker
# 3. 重啟 worker
# 4. 驗證任務重新執行
```

### 場景 3：大量任務壓力測試
```bash
# 啟動測試
make stress-test

# 這會：
# 1. 發送 10000 個任務
# 2. 模擬隨機失敗
# 3. 測量成功率和效能
```

## 監控

### Flower Web UI
```bash
# 啟動 Flower
make monitor

# 訪問 http://localhost:5555
```

### Redis 監控
```bash
# 即時監控 Redis
redis-cli monitor

# 查看 Redis 資訊
redis-cli info
```

## 清理

```bash
# 清理所有資料
make clean

# 清理 Redis 資料
make clean-redis

# 清理測試結果
make clean-results
```

## 注意事項

1. **不要在生產環境執行**：測試包含破壞性操作
2. **資源需求**：至少 2GB RAM，建議 4GB
3. **埠號衝突**：確保 6379（Redis）、5555（Flower）未被佔用
4. **資料備份**：測試前備份重要資料