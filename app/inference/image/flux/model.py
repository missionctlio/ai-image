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

def _load_flux_transformer() -> FluxTransformer2DModel:
    """
    Loads and initializes the FluxTransformer2DModel from the specified URL.

    :return: An instance of FluxTransformer2DModel.
    """
    logger.info(f"Loading FluxTransformer2DModel from URL with dtype {Dtype}...")
    transformer = FluxTransformer2DModel.from_single_file(TRANSFORMER_URL, torch_dtype=Dtype).to("cuda")
    quantize(transformer, weights=qfloat8)
    freeze(transformer)
    logger.info("FluxTransformer2DModel loaded, quantized, and frozen.")
    return transformer

def _load_t5_encoder() -> T5EncoderModel:
    """
    Loads and initializes the T5EncoderModel from the specified repository.

    :return: An instance of T5EncoderModel.
    """
    logger.info(f"Loading T5EncoderModel from {BFL_REPO} with dtype {Dtype}...")
    text_encoder_2 = T5EncoderModel.from_pretrained(BFL_REPO, subfolder="text_encoder_2", torch_dtype=Dtype)
    quantize(text_encoder_2, weights=qfloat8)
    freeze(text_encoder_2)
    logger.info("T5EncoderModel loaded, quantized, and frozen.")
    return text_encoder_2

def _create_flux_pipeline(transformer: FluxTransformer2DModel, text_encoder: T5EncoderModel) -> FluxPipeline:
    """
    Creates and configures a FluxPipeline instance with the given transformer and text encoder.

    :param transformer: The FluxTransformer2DModel instance to use.
    :param text_encoder: The T5EncoderModel instance to use.
    :return: An instance of FluxPipeline.
    """
    logger.info("Loading FluxPipeline...")
    pipe = FluxPipeline.from_pretrained(BFL_REPO, transformer=None, text_encoder_2=None, torch_dtype=Dtype)
    pipe.transformer = transformer
    pipe.text_encoder_2 = text_encoder
    pipe.enable_model_cpu_offload()
    logger.info("FluxPipeline loaded and configured.")
    return pipe

def load_flux_model() -> FluxPipeline:
    """
    Loads and initializes the models required for the pipeline.

    :return: An instance of FluxPipeline configured with the loaded models.
    """
    transformer = _load_flux_transformer()
    text_encoder = _load_t5_encoder()
    pipe = _create_flux_pipeline(transformer, text_encoder)
    return pipe
