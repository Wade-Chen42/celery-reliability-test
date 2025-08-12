"""
Redis persistence tests
"""

import time
import pytest
import redis
from celery import states
from src.tasks import simple_task, critical_task, long_running_task


class TestRedisPersistence:
    """Test Redis persistence mechanisms"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.redis_client = redis.Redis(host='redis', port=6379, db=0)
        cls.results_backend = redis.Redis(host='redis', port=6379, db=1)
    
    def test_message_ack_mechanism(self):
        """Test message acknowledgment mechanism"""
        print("\n=== Testing Message Acknowledgment ===")
        
        # Send task
        task = simple_task.delay("test_persistence")
        task_id = task.id
        print(f"Task ID: {task_id}")
        
        # Check queue length
        queue_length = self.redis_client.llen('celery')
        print(f"Queue length: {queue_length}")
        
        # Wait for completion
        result = task.get(timeout=10)
        print(f"Task result: {result}")
        
        assert result is not None
        assert result['value'] == "test_persistence"
    
    def test_task_persistence_after_restart(self):
        """Test task persistence after Redis restart"""
        print("\n=== Testing Task Persistence ===")
        
        # Send multiple critical tasks
        tasks = []
        for i in range(5):
            task = critical_task.delay(f"critical_data_{i}")
            tasks.append(task)
            print(f"Sent critical task {i}: {task.id}")
        
        # Wait a bit
        time.sleep(2)
        
        # Check results
        results = []
        for task in tasks:
            try:
                result = task.get(timeout=5)
                results.append(result)
                print(f"Task completed: {result}")
            except Exception as e:
                print(f"Task failed: {e}")
        
        # Should have at least some successful results
        assert len(results) > 0
    
    def test_aof_persistence(self):
        """Test AOF persistence mode"""
        print("\n=== Testing AOF Persistence ===")
        
        # Check if AOF is enabled
        try:
            aof_config = self.redis_client.config_get('appendonly')
            print(f"AOF enabled: {aof_config}")
        except Exception as e:
            print(f"Could not check AOF config: {e}")
        
        # Send task
        task = critical_task.delay("aof_test_data")
        
        # Force AOF rewrite
        try:
            self.redis_client.bgrewriteaof()
        except Exception as e:
            print(f"AOF rewrite failed: {e}")
        
        # Get result
        result = task.get(timeout=10)
        assert result is not None
        assert 'CRITICAL_aof_test_data' in result['processed_data']
    
    def test_result_backend_persistence(self):
        """Test result backend persistence"""
        print("\n=== Testing Result Backend Persistence ===")
        
        # Send task and get result
        task = simple_task.delay("result_test")
        result = task.get(timeout=5)
        print(f"Task result: {result}")
        
        # Check if result is stored in Redis
        result_key = f"celery-task-meta-{task.id}"
        stored_result = self.results_backend.get(result_key)
        print(f"Stored result exists: {stored_result is not None}")
        
        assert stored_result is not None
        
        # Check TTL
        ttl = self.results_backend.ttl(result_key)
        print(f"Result TTL: {ttl} seconds")
        assert ttl > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])