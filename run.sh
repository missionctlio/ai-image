#!/bin/bash

# clear cache
sudo sh -c 'sync && echo 3 > /proc/sys/vm/drop_caches'  

# kill any running processes
ps xau |grep venv |awk '{print $2 }'|xargs kill -9

# Check if the virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv .venv
fi

# Activate the virtual environment
source .venv/bin/activate

# Update dependencies
echo "Updating dependencies..."
pip install -r requirements.txt > /dev/null

# Start Docker containers
docker-compose up -d

# Start Celery worker
celery -A app.workers.images worker --loglevel=info --pool=solo &

# Start Flower
celery -A app.workers.images.celery  flower --pool=solo --loglevel=INFO &

# Start Uvicorn server
uvicorn main:app --workers 8 --host 0.0.0.0 --port 8888 --log-level info --reload
