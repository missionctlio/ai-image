from celery import Celery
import os
from app.utils.logging import configure_celery_logging

# Configure JSON logging for Celery
configure_celery_logging()
# Configure Celery
celery = Celery(
    'celery_app',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=['app.workers.celery_config'],
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC'
      # Include this file so tasks are registered
)