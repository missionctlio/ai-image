from app.workers.celery_config import celery
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load LLaMA model 

@celery.task(name='app.workers.images.generate_image_task')
def generate_image_task(prompt: str, aspect_ratio: str):
    from app.inference.image.flux.diffuser import generate_image
    from app.inference.language.llama.description import generate_description
    from app.inference.language.llama.refinement import refined_prompt
    try:
        # Optionally refine the prompt before generating the image
        refined_prompt_text = refined_prompt(prompt)

        # Generate the image based on the refined prompt and aspect ratio
        image_id = generate_image(refined_prompt_text, aspect_ratio)
        
        # Generate the description for the refined prompt
        description = generate_description(refined_prompt_text)

        # Construct the image URL
        image_url = f"/images/original_{image_id}.png"
        
        return {'image_url': image_url, 'description': description}
    except Exception as e:
        # Log the error or handle it as needed
        logger.error(f"Error in generate_image_task: {e}")
        raise e
