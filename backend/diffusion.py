import torch
from diffusers import FluxTransformer2DModel, FluxPipeline, DiffusionPipeline
from transformers import T5EncoderModel
from optimum.quanto import freeze, qfloat8, quantize
import uuid
from PIL import Image
from RealESRGAN import RealESRGAN
import base64
import random

print("Starting script...")

bfl_repo = "black-forest-labs/FLUX.1-dev"
dtype = torch.bfloat16

print(f"Loading FluxTransformer2DModel from URL with dtype {dtype}...")
transformer = FluxTransformer2DModel.from_single_file("https://huggingface.co/Kijai/flux-fp8/blob/main/flux1-dev-fp8.safetensors", torch_dtype=dtype).to("cuda")
# quantize(transformer, weights=qfloat8)
# freeze(transformer)
print("FluxTransformer2DModel loaded.")

print("Quantizing and freezing FluxTransformer2DModel...")
quantize(transformer, weights=qfloat8)
freeze(transformer)
print("FluxTransformer2DModel quantized and frozen.")

print(f"Loading T5EncoderModel from {bfl_repo} with dtype {dtype}...")
text_encoder_2 = T5EncoderModel.from_pretrained(bfl_repo, subfolder="text_encoder_2", torch_dtype=dtype)
print("T5EncoderModel loaded.")

print("Quantizing and freezing T5EncoderModel...")
quantize(text_encoder_2, weights=qfloat8)
freeze(text_encoder_2)
print("T5EncoderModel quantized and frozen.")

print("Loading FluxPipeline...")
pipe = FluxPipeline.from_pretrained(bfl_repo, transformer=None, text_encoder_2=None, torch_dtype=dtype)
pipe.transformer = transformer
pipe.text_encoder_2 = text_encoder_2
pipe.enable_model_cpu_offload()
print("FluxPipeline loaded and configured.")

def generate_image(prompt: str, aspect_ratio: str) -> str:
    print(f"Generating image with prompt: '{prompt}' and aspect ratio: '{aspect_ratio}'")
    
    n_steps = 160
    high_noise_frac = 0.8
    aspect_ratios = {
        "16:9": (960, 544),
        "4:3": (1024, 768),
        "1:1": (1024, 1024),
        "32:9": (1280, 360),
    }
    
    if aspect_ratio not in aspect_ratios:
        print(f"Invalid aspect ratio '{aspect_ratio}'. Defaulting to '1:1'.")
        aspect_ratio = "1:1"  # Default aspect ratio if invalid
    
    initial_width, initial_height = aspect_ratios[aspect_ratio]
    print(f"Using dimensions: width={initial_width}, height={initial_height}")
    
    print("Generating image...")
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
    
    print("Image generated.")
    image_path = f"frontend/images/original_{image_id}.png"
    image.save(image_path)
    print("Upscaling and resizing image...")
    image_s = upscale_and_resize_image(image, 4)
    print("Image resized and upscaled.")
    image_path = f"frontend/images/{image_id}.png"
    image_s.save(image_path)
    print(f"Saving final image to '{image_path}'...")
    print("Image saved.")

    return image_id

def image_to_base64(image) -> str:
    import io

    print("Converting image to base64...")
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    print("Image converted to base64.")
    return img_str

def upscale_and_resize_image(image: Image.Image, scale_factor: int) -> Image.Image:
    """
    Upscales the image using Real-ESRGAN and then resizes it to a final size with a 32:9 aspect ratio.
    """
    print(f"Upscaling image with scale factor {scale_factor}...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    model = RealESRGAN(device, scale=scale_factor)
    model.load_weights('weights/RealESRGAN_x8.pth', download=True)
    print("Real-ESRGAN model initialized and weights loaded.")
    
    sr_image = model.predict(image)
    print("Image upscaled.")
    
    return sr_image
