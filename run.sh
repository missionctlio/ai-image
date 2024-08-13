docker-compose up -d
source .venv/bin/activate
celery -A backend.celery_config.celery worker --pool=solo --loglevel=INFO &
uvicorn backen.main:app  --workers 4 --host 0.0.0.0 --port 8888 --reload-dir backend
