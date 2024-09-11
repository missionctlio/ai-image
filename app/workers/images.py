import logging
import requests
from app.workers.celery_config import celery

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Utility function to handle REST API POST requests
def make_post_request(url: str, payload: dict):
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raises an HTTPError if the response status is 4xx, 5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to {url} failed: {e}")
        return None

@celery.task(name='app.workers.images.generate_image_task')
def generate_image_task(prompt: str, aspect_ratio: str):
    """
    Celery task to generate an image based on a given prompt and aspect ratio.

    Parameters:
    - prompt (str): The text prompt for generating the image.
    - aspect_ratio (str): The desired aspect ratio for the generated image.

    Returns:
    - dict: A dictionary containing:
        - 'image_url' (str): URL of the generated image.

    Raises:
    - Exception: Logs and raises any exceptions encountered during the task execution.
    """
    from app.inference.image.flux.diffuser import generate_image

    try:
        # Generate the image based on the refined or original prompt and aspect ratio
        image_id = generate_image(prompt, aspect_ratio)

        # Construct the image URL
        image_url = f"/images/original_{image_id}.png"

        return {'imageUrl': image_url}
    except Exception as e:
        # Log the error or handle it as needed
        logger.error(f"Error in generate_image_task: {e}")
        raise e
