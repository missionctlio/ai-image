import torch
from diffusers import FluxTransformer2DModel, FluxPipeline
from transformers import T5EncoderModel
from optimum.quanto import freeze, qfloat8, quantize
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BFL_REPO = "black-forest-labs/FLUX.1-dev"
Dtype = torch.bfloat16
TRANSFORMER_URL = "https://huggingface.co/Kijai/flux-fp8/blob/main/flux1-dev-fp8.safetensors"

def load_models() -> FluxPipeline:
    logger.info(f"Loading FluxTransformer2DModel from URL with dtype {Dtype}...")
    transformer = FluxTransformer2DModel.from_single_file(TRANSFORMER_URL, torch_dtype=Dtype).to("cuda")
    quantize(transformer, weights=qfloat8)
    freeze(transformer)
    logger.info("FluxTransformer2DModel loaded, quantized, and frozen.")

    logger.info(f"Loading T5EncoderModel from {BFL_REPO} with dtype {Dtype}...")
    text_encoder_2 = T5EncoderModel.from_pretrained(BFL_REPO, subfolder="text_encoder_2", torch_dtype=Dtype)
    quantize(text_encoder_2, weights=qfloat8)
    freeze(text_encoder_2)
    logger.info("T5EncoderModel loaded, quantized, and frozen.")

    logger.info("Loading FluxPipeline...")
    pipe = FluxPipeline.from_pretrained(BFL_REPO, transformer=None, text_encoder_2=None, torch_dtype=Dtype)
    pipe.transformer = transformer
    pipe.text_encoder_2 = text_encoder_2
    pipe.enable_model_cpu_offload()
    logger.info("FluxPipeline loaded and configured.")
    
    return pipe
