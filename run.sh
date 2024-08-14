#!/bin/bash
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

# Start Uvicorn server
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8888 --reload
