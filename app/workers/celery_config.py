from celery import Celery
import os

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
)

# # Use task name prefix
# celery.conf.task_routes = {
#     'app.workers.*': {'queue': 'default', 'task_prefix': 'celery_task.'}
# }

# # Optional: Define task naming conventions globally
# celery.conf.task_default_exchange = 'default'
# celery.conf.task_default_routing_key = 'celery_task.default'
