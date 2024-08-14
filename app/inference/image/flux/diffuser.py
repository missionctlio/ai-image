import uuid
import random
from PIL import Image
import logging
import torch
from app.inference.image.flux.model import load_models
from app.inference.image.realesrgan.rescaler import upscale_and_resize_image

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize pipeline
pipe = load_models()

def generate_image(prompt: str, aspect_ratio: str) -> str:
    logger.info(f"Generating image with prompt: '{prompt}' and aspect ratio: '{aspect_ratio}'")
    
    aspect_ratios = {
        "16:9": (960, 544),
        "4:3": (1024, 768),
        "1:1": (1024, 1024),
        "32:9": (1280, 360),
    }
    
    if aspect_ratio not in aspect_ratios:
        logger.warning(f"Invalid aspect ratio '{aspect_ratio}'. Defaulting to '1:1'.")
        aspect_ratio = "1:1"  # Default aspect ratio if invalid
    
    initial_width, initial_height = aspect_ratios[aspect_ratio]
    logger.info(f"Using dimensions: width={initial_width}, height={initial_height}")
    
    logger.info("Generating image...")
    image = pipe(
        prompt=prompt,
        guidance_scale=100,
        height=initial_height,
        max_sequence_length=255,
        width=initial_width,
        num_inference_steps=14,
        generator=torch.Generator("cpu").manual_seed(random.randint(1, 123456))
    ).images[0]
        
    image_id = str(uuid.uuid4())
    
    logger.info("Image generated.")
    image_path = f"frontend/images/original_{image_id}.png"
    image.save(image_path)
    logger.info("Upscaling and resizing image...")
    
    # Use function from rescaler package
    image_s = upscale_and_resize_image(image, 4)
    
    logger.info("Image resized and upscaled.")
    image_path = f"frontend/images/{image_id}.png"
    image_s.save(image_path)
    logger.info(f"Saving final image to '{image_path}'...")
    logger.info("Image saved.")

    return image_id
