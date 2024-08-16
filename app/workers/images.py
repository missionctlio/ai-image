from app.workers.celery_config import celery
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@celery.task(name='app.workers.images.generate_image_task')
def generate_image_task(prompt: str, aspect_ratio: str, usePromptRefiner: bool):
    """
    Celery task to generate an image based on a given prompt and aspect ratio.

    Parameters:
    - prompt (str): The text prompt for generating the image.
    - aspect_ratio (str): The desired aspect ratio for the generated image.
    - usepromptrefiner (bool): A flag indicating whether to refine the prompt or not.

    Returns:
    - dict: A dictionary containing:
        - 'image_url' (str): URL of the generated image.
        - 'refined_prompt' (str): The refined prompt used for generating the image, or {prompt} if not refined.
        - 'description' (str): Description of the image based on the refined prompt

    Raises:
    - Exception: Logs and raises any exceptions encountered during the task execution.
    """
    from app.inference.language.llama.description import generate_description
    from app.inference.language.llama.refinement import refined_prompt
    from app.inference.image.flux.diffuser import generate_image
    
    try:
        # Refine the prompt if usepromptrefiner is True
        refined_prompt_text = refined_prompt(prompt) if usePromptRefiner else prompt
        # Generate the image based on the refined or original prompt and aspect ratio
        image_id = generate_image(refined_prompt_text, aspect_ratio)
        # Generate the description if prompt was refined
        description = generate_description(refined_prompt_text)
        # Construct the image URL
        image_url = f"/images/original_{image_id}.png"
        
        return {'imageUrl': image_url, 'refinedPrompt': refined_prompt_text, 'description': description}
    except Exception as e:
        # Log the error or handle it as needed
        logger.error(f"Error in generate_image_task: {e}")
        raise e
