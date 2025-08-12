#!/usr/bin/env python3
"""
Check Celery queue status
"""

import redis
import json
from tabulate import tabulate


def main():
    """Check queue status"""
    try:
        # Connect to Redis
        redis_client = redis.Redis(host='redis', port=6379, db=0)
        
        # Check connection
        redis_client.ping()
        
        # Get queue information
        queues = ['default', 'critical', 'batch']
        queue_info = []
        
        for queue in queues:
            length = redis_client.llen(queue)
            queue_info.append([queue, length])
        
        # Print queue status
        print("Queue Status:")
        print(tabulate(queue_info, headers=['Queue', 'Length'], tablefmt='grid'))
        
        # Get Redis info
        info = redis_client.info()
        print(f"\nRedis Status:")
        print(f"Connected clients: {info.get('connected_clients', 'N/A')}")
        print(f"Used memory: {info.get('used_memory_human', 'N/A')}")
        print(f"Keys: {redis_client.dbsize()}")
        
    except Exception as e:
        print(f"Error checking queues: {e}")


if __name__ == "__main__":
    main()