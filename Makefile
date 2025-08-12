# Celery Reliability Test Makefile

.PHONY: help setup up down test-all clean

# 顏色定義
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## 顯示幫助訊息
	@echo "$(GREEN)Celery Reliability Test Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# 環境設置
setup: ## 初始化測試環境
	@echo "$(GREEN)Setting up test environment...$(NC)"
	python -m venv venv
	./venv/bin/pip install -r requirements.txt
	mkdir -p redis/data results
	@echo "$(GREEN)Setup complete!$(NC)"

# Docker 操作
up: ## 啟動所有服務
	docker-compose up -d
	@echo "$(GREEN)Services started! Flower UI: http://localhost:5555$(NC)"

down: ## 停止所有服務
	docker-compose down
	@echo "$(YELLOW)Services stopped$(NC)"

restart: ## 重啟所有服務
	docker-compose restart
	@echo "$(GREEN)Services restarted$(NC)"

logs: ## 查看所有服務日誌
	docker-compose logs -f

# 測試執行
test-all: ## 執行所有測試
	@echo "$(GREEN)Running all tests...$(NC)"
	docker-compose exec test-runner python -m pytest tests/ -v

test-persistence: ## 測試 Redis 持久化
	@echo "$(GREEN)Testing Redis persistence...$(NC)"
	docker-compose exec test-runner python tests/test_persistence.py

test-retry: ## 測試重試機制
	@echo "$(GREEN)Testing retry mechanism...$(NC)"
	docker-compose exec test-runner python tests/test_retry.py

test-recovery: ## 測試恢復機制
	@echo "$(GREEN)Testing recovery mechanism...$(NC)"
	docker-compose exec test-runner python tests/test_recovery.py

test-pipeline: ## 測試 Pipeline
	@echo "$(GREEN)Testing pipeline...$(NC)"
	docker-compose exec test-runner python tests/test_pipeline.py

# 壓力測試
stress-test: ## 執行壓力測試 (TASKS=1000 BATCH_SIZE=100)
	@echo "$(YELLOW)Starting stress test ($(TASKS) tasks, batch size $(BATCH_SIZE))...$(NC)"
	docker-compose exec test-runner python scripts/stress_test.py --tasks $(or $(TASKS),1000) --batch-size $(or $(BATCH_SIZE),100)

# 崩潰模擬
test-redis-crash: ## 模擬 Redis 崩潰
	@echo "$(RED)Simulating Redis crash...$(NC)"
	./scripts/simulate_crash.sh redis

test-worker-crash: ## 模擬 Worker 崩潰
	@echo "$(RED)Simulating Worker crash...$(NC)"
	./scripts/simulate_crash.sh worker

# 監控
monitor: ## 啟動監控（Flower）
	@echo "$(GREEN)Opening Flower monitoring UI...$(NC)"
	open http://localhost:5555 || xdg-open http://localhost:5555

redis-monitor: ## 監控 Redis
	docker-compose exec redis redis-cli monitor

redis-info: ## 查看 Redis 資訊
	docker-compose exec redis redis-cli info

# 清理
clean: ## 清理所有資料
	@echo "$(YELLOW)Cleaning all data...$(NC)"
	docker-compose down -v
	rm -rf redis/data/* results/*
	@echo "$(GREEN)Cleanup complete$(NC)"

clean-redis: ## 清理 Redis 資料
	docker-compose exec redis redis-cli FLUSHALL
	@echo "$(GREEN)Redis data cleared$(NC)"

clean-results: ## 清理測試結果
	rm -rf results/*
	@echo "$(GREEN)Test results cleared$(NC)"

# 報告
report: ## 生成測試報告
	@echo "$(GREEN)Generating test report...$(NC)"
	docker-compose exec test-runner python scripts/generate_report.py
	@echo "$(GREEN)Report saved to results/test_report.html$(NC)"

# 開發工具
shell: ## 進入測試容器 shell
	docker-compose exec test-runner /bin/bash

redis-cli: ## 進入 Redis CLI
	docker-compose exec redis redis-cli

worker-shell: ## 進入 Worker 容器 shell
	docker-compose exec worker1 /bin/bash

# 狀態檢查
status: ## 檢查服務狀態
	@echo "$(GREEN)Service Status:$(NC)"
	docker-compose ps
	@echo "\n$(GREEN)Redis Status:$(NC)"
	docker-compose exec redis redis-cli ping || echo "$(RED)Redis is down$(NC)"
	@echo "\n$(GREEN)Queue Status:$(NC)"
	docker-compose exec test-runner python scripts/check_queues.py

watch: ## 即時監控隊列狀態 (按 Ctrl+C 停止)
	@echo "$(GREEN)Starting queue monitor... Press Ctrl+C to stop$(NC)"
	@while true; do \
		clear; \
		echo "$(GREEN)=== Queue Monitor $$(date) ===$(NC)"; \
		docker-compose exec test-runner python scripts/check_queues.py; \
		sleep 0.5; \
	done

test-persistence: ## 測試 Redis 持久化
	@echo "$(YELLOW)Testing Redis persistence...$(NC)"
	@echo "1. Stopping workers..."
	docker-compose stop worker1 worker2
	@echo "2. Sending tasks..."
	make stress-test TASKS=200 BATCH_SIZE=20
	@echo "3. Current queue status:"
	make status
	@echo "4. Simulating system crash..."
	docker-compose down
	@echo "5. Restarting system..."
	docker-compose up -d
	@sleep 10
	@echo "6. Queue status after restart:"
	make status

test-retry: ## 測試重試機制
	@echo "$(YELLOW)Testing retry mechanism...$(NC)"
	docker-compose exec test-runner python -c "from src.tasks import failing_task; task = failing_task.delay(2); print('Task ID:', task.id); result = task.get(timeout=30); print('Result:', result)"
	@echo "$(GREEN)Check logs for retry attempts:$(NC)"
	docker-compose logs worker1 | grep "failing_task" | tail -10