import torch
from diffusers import FluxPipeline
from PIL import Image as PIL
import logging
import random
import torch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

torch.cuda.empty_cache()

"""
Loads and initializes the models required for the pipeline.

:return: An instance of FluxPipeline configured with the loaded models.
"""
pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16)
pipe.enable_sequential_cpu_offload()
pipe.vae.enable_slicing()
pipe.vae.enable_tiling()

def generate_image(prompt: str, initial_width: int, initial_height: int) -> PIL:
    """
    Generates an image based on a prompt and aspect ratio, then upscales and saves the image.

    :param prompt: The text prompt to generate the image.
    :param aspect_ratio: The desired aspect ratio of the generated image (e.g., '16:9', '4:3').
    :return: A unique identifier for the generated image.
    """
    logger.info(f"Generating image with prompt: '{prompt}' and dimensions: '{initial_width}x{initial_height}'")
    image = pipe(
        prompt=prompt,
        guidance_scale=100,
        height=initial_height,
        max_sequence_length=255,
        width=initial_width,
        num_inference_steps=6,
        generator=torch.Generator("cpu").manual_seed(random.randint(1, 123456))
    ).images[0]
    return image
