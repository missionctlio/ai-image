from accelerate import Accelerator
from diffusers import DiffusionPipeline
import torch
import uuid
from RealESRGAN import RealESRGAN
from PIL import Image
import numpy as np

# Initialize Accelerator
accelerator = Accelerator()

# Load both base & refiner pipelines with accelerator support
base = DiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0", 
    torch_dtype=torch.float16, 
    variant="fp16", 
    use_safetensors=True
)
base.enable_model_cpu_offload()

refiner = DiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-refiner-1.0",
    text_encoder_2=base.text_encoder_2,
    vae=base.vae,
    torch_dtype=torch.float16,
    use_safetensors=True,
    variant="fp16",
)
refiner.enable_model_cpu_offload()

def generate_image(prompt: str) -> str:
    n_steps = 160
    high_noise_frac = 0.8
    aspect_ratio = 32 / 9
    initial_width = 2048
    initial_height = int(initial_width / aspect_ratio)
    
    # Generate the image at the calculated size (2048x576 for 32:9)
    image = base(
        prompt=prompt,
        num_inference_steps=n_steps,
        denoising_end=high_noise_frac,
        output_type="latent",  # Output as a PIL Image
        # height=initial_height,
        # width=initial_width,
    ).images[0]
    
    # Optionally refine the image
    image = refiner(
        prompt=prompt,
        num_inference_steps=n_steps,
        denoising_start=high_noise_frac,
        image=image,
    ).images[0]
      # Upscale and resize the image

    # Save the image with a unique UUID
    image_id = str(uuid.uuid4())
    image_path = f"frontend/images/{image_id}.png"
    image_s = upscale_and_resize_image(image, 4)
    image_s.save(image_path)

    # Return the relative path to the image
    return image_id

def image_to_base64(image) -> str:
    import io
    from PIL import Image
    import base64

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

def upscale_and_resize_image(image: Image.Image, scale_factor: int) -> Image.Image:
    """
    Upscales the image using Real-ESRGAN and then resizes it to a final size with a 32:9 aspect ratio.
    """
    # Upscale the image
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = RealESRGAN(device, scale=scale_factor)
    model.load_weights('weights/RealESRGAN_x4.pth', download=True)
    
    # Predict returns a PIL Image, no need to convert it again
    sr_image = model.predict(image)
    
    return sr_image
