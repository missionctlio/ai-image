for x in `cat .env`;do export $x;done
source .venv/bin/activate
celery -A backend.celery_config.celery worker --pool=solo --loglevel=INFO &
uvicorn backend.main:app  --workers 4 --host 0.0.0.0 --port 8888 --reload-dir backend
