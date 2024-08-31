import uuid
from PIL import Image
import logging
from app.inference.image.flux.model import FluxPipelineManager
from app.inference.image.realesrgan.rescaler import upscale_and_resize_image

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_aspect_ratio_dimensions(aspect_ratio: str) -> tuple:
    """
    Retrieves the dimensions for the given aspect ratio.

    :param aspect_ratio: The aspect ratio string (e.g., '16:9', '4:3').
    :return: A tuple containing the width and height for the specified aspect ratio.
    """
    aspect_ratios = {
        "1:1": (1024, 1024),
        "3:2": (1504, 1008),
        "4:3": (1024, 768),
        "16:9": (960, 540),
        "21:9": (2560, 1080),
        "32:9": (1280, 360),
    }
    
    if aspect_ratio not in aspect_ratios:
        logger.warning(f"Invalid aspect ratio '{aspect_ratio}'. Defaulting to '1:1'.")
        aspect_ratio = "1:1"  # Default aspect ratio if invalid

    return aspect_ratios[aspect_ratio]

def generate_image(prompt: str, aspect_ratio: str) -> str:
    """
    Generates an image based on a prompt and aspect ratio, then upscales and saves the image.

    :param prompt: The text prompt to generate the image.
    :param aspect_ratio: The desired aspect ratio of the generated image (e.g., '16:9', '4:3').
    :return: A unique identifier for the generated image.
    """
    logger.info(f"Generating image with prompt: '{prompt}' and aspect ratio: '{aspect_ratio}'")

    initial_width, initial_height = _get_aspect_ratio_dimensions(aspect_ratio)
    logger.info(f"Using dimensions: width={initial_width}, height={initial_height}")

    logger.info("Generating image...")
   
    pipe = FluxPipelineManager()
    pipe.initialize_pipeline()
    image = pipe.generate_image(prompt,initial_width,initial_height)   

    image_id = str(uuid.uuid4())   

    image_id = str(uuid.uuid4())
    _save_image(image, image_id)  # Save the original image
    
    logger.info("Upscaling and resizing image...")
    image_s = upscale_and_resize_image(image, 4)
    _save_image(image_s, image_id, is_upscaled=True)  # Save the upscaled image
    
    return image_id

def _save_image(image: Image.Image, image_id: str, is_upscaled: bool = False) -> None:
    """
    Saves the given image to a file.

    :param image: The PIL Image to save.
    :param image_id: Unique identifier for the image.
    :param is_upscaled: If True, saves the image without a prefix.
    """
    prefix = "" if is_upscaled else "original_"
    image_path = f"frontend/images/{prefix}{image_id}.png"
    image.save(image_path)
    logger.info(f"Saving image to '{image_path}'...")
    logger.info("Image saved.")
