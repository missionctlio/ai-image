from PIL import Image
import logging
from app.inference.image.realesrgan.model import load_realesrgan_model

# Setup logging
logger = logging.getLogger(__name__)

pipe = load_realesrgan_model(scale_factor=4)

def upscale_and_resize_image(image: Image.Image, scale_factor: int) -> Image.Image:
    """
    Upscales the image using Real-ESRGAN.
    """
    logger.info(f"Upscaling image with scale factor {scale_factor}...")
    image = pipe.predict(image)
    logger.info("Image upscaled.")
    return image
