#!/usr/bin/env python3
"""Celery stress test script.

Tests the performance and stability of Celery + Redis system under heavy task loads.
"""

import argparse
import sys
import time
from src.tasks import batch_task

# Add application root directory to Python path to import src modules
sys.path.append('/app')



def run_stress_test(num_tasks=1000, batch_size=100):
    """Run stress test with specified parameters.
    
    Args:
        num_tasks: Total number of tasks to execute, defaults to 1000.
        batch_size: Number of tasks per batch, defaults to 100.
    """
    print(f"Starting stress test with {num_tasks} tasks...")
    
    # Record test start time
    start_time = time.time()
    tasks = []  # Store task references for result collection
    
    # Send tasks in batches to avoid overwhelming the system with simultaneous requests
    for batch in range(0, num_tasks, batch_size):
        batch_tasks = []
        # Calculate current batch end position, ensuring we don't exceed total tasks
        batch_end = min(batch + batch_size, num_tasks)
        
        print(f"Sending batch {batch//batch_size + 1} ({batch_end - batch} tasks)...")
        
        # Create and send individual tasks within current batch
        for i in range(batch, batch_end):
            # Use delay() method to asynchronously send task to Celery queue
            task = batch_task.delay(f"batch_{batch//batch_size + 1}", i, f"data_{i}")
            batch_tasks.append(task)
        
        # Add batch tasks to total task list
        tasks.extend(batch_tasks)
        
        # Brief delay between batches to prevent instant massive requests
        time.sleep(0.1)
    
    # Calculate task sending duration
    send_time = time.time() - start_time
    print(f"All tasks sent in {send_time:.2f} seconds")
    
    # Wait for and collect task execution results
    print("Waiting for results...")
    completed = 0  # Number of successfully completed tasks
    failed = 0     # Number of failed tasks
    
    # Check execution status of each task individually
    for task in tasks:
        try:
            # Use get() method to wait for task completion with 1 second timeout
            task.get(timeout=1)
            completed += 1
        except Exception:
            # Task execution failed or timed out
            failed += 1
    
    # Calculate total execution time
    total_time = time.time() - start_time
    
    # Output test result statistics
    print(f"\nStress Test Results:")
    print(f"Total tasks: {num_tasks}")
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {completed/num_tasks*100:.2f}%")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Tasks per second: {num_tasks/total_time:.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Celery stress test')
    parser.add_argument('--tasks', type=int, default=1000, help='Number of tasks to send')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for sending tasks')
    
    args = parser.parse_args()
    
    run_stress_test(args.tasks, args.batch_size)