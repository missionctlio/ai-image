# celery_config.py

from celery import Celery
import os
# Initialize Celery
celery = Celery(
    'celery_app',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=['backend.celery_config']  # Include this file so tasks are registered
)

@celery.task(name='backend.celery_config.generate_image_task')
def generate_image_task(prompt: str, aspect_ratio: str):
    from backend.diffusion import generate_image
    try:
        image_id = generate_image(prompt, aspect_ratio)
        image_url = f"/images/original_{image_id}.png"
        return {'image_url': image_url, 'description': "N/A"}
    except Exception as e:
        raise e