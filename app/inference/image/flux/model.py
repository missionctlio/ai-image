import os
import torch
from diffusers import FluxTransformer2DModel, FluxPipeline
from transformers import T5EncoderModel
from optimum.quanto import freeze, qfloat8, quantize
from PIL import Image as PIL
import logging
import random

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Clear CUDA memory
torch.cuda.empty_cache()
logger.info("CUDA memory cleared.")

# Check the flux_version environment variable
flux_version = os.getenv("FLUX_VERSION", "default_version")
logger.info(f"FLUX_VERSION environment variable is set to: {flux_version}")

if flux_version == "schnell":
    NUM_STEPS = 4
    logger.info("Initializing Schnell model pipeline.")
    pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16)
    logger.info("Schnell model pipeline loaded successfully.")
    pipe.enable_sequential_cpu_offload()
    logger.info("Sequential CPU offload enabled for Schnell pipeline.")
    pipe.vae.enable_slicing()
    logger.info("VAE slicing enabled for Schnell pipeline.")
    pipe.vae.enable_tiling()
    logger.info("VAE tiling enabled for Schnell pipeline.")
else:
    NUM_STEPS = 16
    logger.info("Initializing FluxTransformer2DModel and text encoder for default pipeline.")
    bfl_repo = "black-forest-labs/FLUX.1-dev"
    dtype = torch.bfloat16
    transformer = FluxTransformer2DModel.from_single_file("https://huggingface.co/Kijai/flux-fp8/blob/main/flux1-dev-fp8.safetensors", torch_dtype=dtype)
    logger.info("FluxTransformer2DModel loaded from single file.")
    quantize(transformer, weights=qfloat8)
    logger.info("Quantization applied to transformer model.")
    freeze(transformer)
    logger.info("Transformer model weights frozen.")
    text_encoder_2 = T5EncoderModel.from_pretrained(bfl_repo, subfolder="text_encoder_2", torch_dtype=dtype)
    logger.info("T5EncoderModel loaded from pre-trained repository.")
    quantize(text_encoder_2, weights=qfloat8)
    logger.info("Quantization applied to text encoder.")
    freeze(text_encoder_2)
    logger.info("Text encoder weights frozen.")
    pipe = FluxPipeline.from_pretrained(bfl_repo, transformer=None, text_encoder_2=None, torch_dtype=dtype)
    pipe.transformer = transformer
    pipe.text_encoder_2 = text_encoder_2
    logger.info("FluxPipeline initialized with custom transformer and text encoder.")
    pipe.enable_model_cpu_offload()
    logger.info("Model CPU offload enabled for default pipeline.")

def generate_image(prompt: str, initial_width: int, initial_height: int) -> PIL:
    """
    Generates an image based on a prompt and aspect ratio, then upscales and saves the image.

    :param prompt: The text prompt to generate the image.
    :param initial_width: The width of the generated image.
    :param initial_height: The height of the generated image.
    :return: The generated image.
    """
    logger.info(f"Generating image with prompt: '{prompt}' and dimensions: '{initial_width}x{initial_height}'")
    image = pipe(
        prompt=prompt,
        guidance_scale=100,
        height=initial_height,
        max_sequence_length=255,
        width=initial_width,
        num_inference_steps=NUM_STEPS,
        generator=torch.Generator("cpu").manual_seed(random.randint(1, 123456))
    ).images[0]
    logger.info("Image generated successfully.")
    return image