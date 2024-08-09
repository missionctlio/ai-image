# backend/diffusion.py

from diffusers import DiffusionPipeline
from diffusers.utils import pt_to_pil
import torch
import io
import base64

# Function to get the appropriate device
def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Initialize device
device = get_device()
print(f"Using device: {device}")

# Load diffusion models
print("Loading diffusion models...")
stage_1 = DiffusionPipeline.from_pretrained("DeepFloyd/IF-I-XL-v1.0", variant="fp16", torch_dtype=torch.float16)
stage_1.to(device)
stage_1.enable_model_cpu_offload()

stage_2 = DiffusionPipeline.from_pretrained("DeepFloyd/IF-II-L-v1.0", text_encoder=None, variant="fp16", torch_dtype=torch.float16)
stage_2.to(device)
stage_2.enable_model_cpu_offload()

safety_modules = {"feature_extractor": stage_1.feature_extractor}
stage_3 = DiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-x4-upscaler", **safety_modules, torch_dtype=torch.float16)
stage_3.to(device)
stage_3.enable_model_cpu_offload()

print("Diffusion models loaded and moved to device.")

def generate_image(prompt: str) -> str:
    print("Generating image for prompt:", prompt)
    generator = torch.manual_seed(0)

    print("Encoding prompt...")
    # Text embeddings
    prompt_embeds, negative_embeds = stage_1.encode_prompt(prompt)

    print("Running Stage 1...")
    # Stage 1
    stage_1_output = stage_1(
        prompt_embeds=prompt_embeds, 
        negative_prompt_embeds=negative_embeds, 
        generator=generator, 
        output_type="pt"
    ).images
    print("Stage 1 completed.")

    # Move intermediate results to CPU if needed
    if torch.cuda.is_available():
        stage_1_output = [img.cpu() for img in stage_1_output]

    print("Running Stage 2...")
    # Stage 2
    stage_2_output = stage_2(
        image=stage_1_output,
        prompt_embeds=prompt_embeds,
        negative_prompt_embeds=negative_embeds,
        generator=generator,
        output_type="pt",
    ).images
    print("Stage 2 completed.")

    # Move intermediate results to CPU if needed
    if torch.cuda.is_available():
        stage_2_output = [img.cpu() for img in stage_2_output]

    print("Running Stage 3...")
    # Stage 3
    stage_3_output = stage_3(prompt=prompt, image=stage_2_output, noise_level=100, generator=generator).images
    print("Stage 3 completed.")

    print("Converting image to PIL format and encoding to base64...")
    # Convert the tensor to PIL image
    if isinstance(stage_3_output[0], torch.Tensor):
        img_pil = pt_to_pil(stage_3_output[0])
    else:
        img_pil = stage_3_output[0]  # Assuming it's already a PIL image

    buffered = io.BytesIO()
    img_pil.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    print("Image conversion and encoding completed.")

    return img_str
