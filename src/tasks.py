"""
Test tasks for Celery reliability testing
"""

import time
import random
import logging
from typing import Any, Dict
from celery import Task
from src.celery_app import app

logger = logging.getLogger(__name__)


class BaseTask(Task):
    """Base task class with common functionality"""
    
    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        logger.info(f"Task {task_id} succeeded: {retval}")
    
    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        logger.error(f"Task {task_id} failed: {exc}")
    
    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        logger.warning(f"Task {task_id} retrying: {exc}")


@app.task(bind=True, base=BaseTask)
def simple_task(self, value: Any) -> Dict[str, Any]:
    """Simple task for basic testing"""
    logger.info(f"Executing simple_task with value: {value}")
    return {
        'task_id': self.request.id,
        'value': value,
        'timestamp': time.time()
    }


@app.task(bind=True, base=BaseTask, autoretry_for=(Exception,), 
         retry_kwargs={'max_retries': 3, 'countdown': 2})
def failing_task(self, fail_count: int = 2) -> Dict[str, Any]:
    """Task that fails a specified number of times before succeeding"""
    retry_count = self.request.retries
    logger.info(f"failing_task attempt {retry_count + 1}")
    
    if retry_count < fail_count:
        raise Exception(f"Intentional failure (attempt {retry_count + 1})")
    
    return {
        'task_id': self.request.id,
        'total_attempts': retry_count + 1,
        'success': True
    }


@app.task(bind=True, base=BaseTask)
def long_running_task(self, duration: int = 30, checkpoint_interval: int = 5) -> Dict[str, Any]:
    """Long-running task with progress tracking"""
    task_id = self.request.id
    logger.info(f"Starting long_running_task {task_id} for {duration}s")
    
    checkpoints = []
    for i in range(0, duration, checkpoint_interval):
        current_time = min(i + checkpoint_interval, duration)
        
        # Simulate work
        time.sleep(min(checkpoint_interval, duration - i))
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': current_time, 'total': duration}
        )
        
        checkpoint = {'progress': current_time, 'total': duration}
        checkpoints.append(checkpoint)
        logger.info(f"Task {task_id} checkpoint: {checkpoint}")
    
    return {
        'task_id': task_id,
        'checkpoints': checkpoints,
        'duration': duration,
        'completed': True
    }


@app.task(bind=True, base=BaseTask)
def critical_task(self, data: Any) -> Dict[str, Any]:
    """Critical task that must not be lost"""
    logger.info(f"Executing critical_task with data: {data}")
    
    # Simulate important processing
    time.sleep(2)
    
    result = {
        'task_id': self.request.id,
        'processed_data': f"CRITICAL_{data}",
        'timestamp': time.time()
    }
    
    return result


@app.task(bind=True, base=BaseTask)
def memory_task(self, key: str, operation: str = 'store', value: Any = None) -> Dict[str, Any]:
    """Task for testing state persistence"""
    if operation == 'store':
        app.backend.set(key, value, timeout=3600)
        logger.info(f"Stored data with key: {key}")
        return {'stored': True, 'key': key, 'value': value}
    
    elif operation == 'retrieve':
        stored_value = app.backend.get(key)
        logger.info(f"Retrieved data for key {key}: {stored_value}")
        return {'retrieved': stored_value, 'key': key}
    
    else:
        raise ValueError(f"Unknown operation: {operation}")


@app.task(bind=True, base=BaseTask)
def batch_task(self, batch_id: str, item_id: int, data: Any) -> Dict[str, Any]:
    """Task for batch processing testing"""
    logger.info(f"Processing batch {batch_id}, item {item_id}")
    
    # Random processing time
    time.sleep(random.uniform(0.1, 1.0))
    
    # Random failure (10% chance)
    if random.random() < 0.1:
        raise Exception(f"Random failure in batch {batch_id}, item {item_id}")
    
    return {
        'batch_id': batch_id,
        'item_id': item_id,
        'processed_data': f"processed_{data}",
        'timestamp': time.time()
    }


@app.task(bind=True, base=BaseTask)
def health_check(self) -> Dict[str, Any]:
    """Health check task"""
    return {
        'status': 'healthy',
        'timestamp': time.time(),
        'worker': self.request.hostname
    }


@app.task(bind=True, base=BaseTask)
def pipeline_step(self, step_number: int, input_data: Any) -> Dict[str, Any]:
    """Pipeline step for chain testing"""
    logger.info(f"Executing pipeline step {step_number} with input: {input_data}")
    
    # Simulate processing
    time.sleep(1)
    
    # Step 3 has 20% chance of failure
    if step_number == 3 and random.random() < 0.2:
        raise Exception(f"Pipeline step {step_number} failed")
    
    output = {
        'step': step_number,
        'input': input_data,
        'output': f"step_{step_number}_processed_{input_data}"
    }
    
    return output


@app.task(bind=True)
def aggregator_task(self, results: list) -> Dict[str, Any]:
    """Aggregator for chord testing"""
    logger.info(f"Aggregating {len(results)} results")
    
    return {
        'aggregated_results': results,
        'total_items': len(results),
        'timestamp': time.time()
    }


# Utility functions for creating workflows
def create_test_chain(initial_data: Any, steps: int = 3):
    """Create a test chain workflow"""
    from celery import chain
    
    workflow = chain(
        pipeline_step.s(1, initial_data)
    )
    
    for i in range(2, steps + 1):
        workflow = workflow | pipeline_step.s(i)
    
    return workflow


def create_test_group(data_list: list):
    """Create a test group workflow"""
    from celery import group
    
    return group(
        simple_task.s(data) for data in data_list
    )


def create_test_chord(data_list: list):
    """Create a test chord workflow"""
    from celery import chord, group
    
    parallel_tasks = group(
        simple_task.s(data) for data in data_list
    )
    
    return chord(parallel_tasks)(aggregator_task.s())