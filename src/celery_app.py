"""
Celery Application Configuration for Testing
"""

import os
from celery import Celery
from kombu import Queue
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 建立 Celery 應用
app = Celery('celery_reliability_test')

# 配置
app.conf.update(
    # Broker 和 Backend
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
    
    # 序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # 重要：可靠性配置
    task_acks_late=True,  # 任務完成後才確認
    task_reject_on_worker_lost=True,  # Worker 丟失時拒絕任務
    worker_prefetch_multiplier=1,  # 每次只預取一個任務
    
    # 任務配置
    task_track_started=True,
    task_send_sent_event=True,
    result_persistent=True,
    result_expires=3600,
    
    # 重試配置
    task_default_retry_delay=10,
    task_max_retries=3,
    
    # Queue 配置
    task_default_queue='default',
    task_queues=(
        Queue('default', routing_key='task.#'),
        Queue('critical', routing_key='critical.#'),
        Queue('batch', routing_key='batch.#'),
    ),
    
    # 時間限制
    task_time_limit=300,  # 5 分鐘
    task_soft_time_limit=240,  # 4 分鐘
    
    # Worker 配置
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Beat 配置（定時任務）
    beat_schedule={
        'health-check': {
            'task': 'src.tasks.health_check',
            'schedule': 30.0,  # 每 30 秒
        },
    },
)

# 自動發現任務
app.autodiscover_tasks(['src.tasks'])

if __name__ == '__main__':
    app.start()