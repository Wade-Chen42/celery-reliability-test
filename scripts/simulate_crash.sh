#!/bin/bash

# 模擬服務崩潰腳本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SERVICE=$1

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 [redis|worker|all]"
    exit 1
fi

echo -e "${YELLOW}Starting crash simulation for: $SERVICE${NC}"

case $SERVICE in
    redis)
        echo -e "${RED}Killing Redis...${NC}"
        docker-compose stop redis
        sleep 2
        
        echo -e "${YELLOW}Waiting 5 seconds...${NC}"
        sleep 5
        
        echo -e "${GREEN}Restarting Redis...${NC}"
        docker-compose start redis
        sleep 3
        
        echo -e "${GREEN}Redis recovered!${NC}"
        docker-compose exec redis redis-cli ping
        ;;
        
    worker)
        echo -e "${RED}Killing Worker 1...${NC}"
        docker-compose stop worker1
        sleep 2
        
        echo -e "${YELLOW}Waiting 5 seconds...${NC}"
        sleep 5
        
        echo -e "${GREEN}Restarting Worker 1...${NC}"
        docker-compose start worker1
        sleep 3
        
        echo -e "${GREEN}Worker recovered!${NC}"
        ;;
        
    all)
        echo -e "${RED}Killing all services...${NC}"
        docker-compose stop
        sleep 2
        
        echo -e "${YELLOW}Waiting 5 seconds...${NC}"
        sleep 5
        
        echo -e "${GREEN}Restarting all services...${NC}"
        docker-compose start
        sleep 5
        
        echo -e "${GREEN}All services recovered!${NC}"
        docker-compose ps
        ;;
        
    *)
        echo "Unknown service: $SERVICE"
        echo "Valid options: redis, worker, all"
        exit 1
        ;;
esac

echo -e "${GREEN}Crash simulation completed!${NC}"