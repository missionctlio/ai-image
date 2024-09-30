from PIL import Image
import logging
import torch
import logging
from diffusers import FluxControlNetModel, FluxControlNetPipeline

# Setup logging
logger = logging.getLogger(__name__)

def load_fluxcontrolnet_model():
    """
    Initializes and returns a FluxControlNet model.
    """
    logger.info("Initializing FluxControlNet model...")
    
    # Use bfloat16 for better memory efficiency
    controlnet = FluxControlNetModel.from_pretrained(
        "jasperai/Flux.1-dev-Controlnet-Upscaler",
        torch_dtype=torch.bfloat16
    )
    
    # Create the pipeline using the controlnet
    pipe = FluxControlNetPipeline.from_pretrained(
        "black-forest-labs/FLUX.1-dev",
        controlnet=controlnet,
        torch_dtype=torch.bfloat16
    )
    
    # Move the pipeline to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    pipe.to(device)
    logger.info(f"Model initialized and moved to device: {device}")
    
    return pipe

pipe = load_fluxcontrolnet_model()

def upscale_and_resize_image(image: Image.Image, scale_factor: int) -> Image.Image:
    """
    Upscales the image using FluxControlNet.
    """
    logger.info(f"Upscaling image with scale factor {scale_factor}...")

    # Resize the control image to the desired upscale factor
    w, h = image.size
    control_image = image.resize((w * scale_factor, h * scale_factor))

    # Run the model
    output = pipe(
        prompt="",  # Can be modified for specific text-guided upscaling
        control_image=control_image,
        controlnet_conditioning_scale=0.6,  # Customize this as needed
        num_inference_steps=28,
        guidance_scale=3.5,
        height=control_image.size[1],
        width=control_image.size[0]
    ).images[0]
    
    logger.info("Image upscaled.")
    return output