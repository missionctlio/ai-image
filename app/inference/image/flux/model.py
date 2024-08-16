import torch
from diffusers import FluxTransformer2DModel, FluxPipeline
from transformers import T5EncoderModel
from optimum.quanto import freeze, qfloat8, quantize
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_flux_model() -> FluxPipeline:
    """
    Loads and initializes the models required for the pipeline.

    :return: An instance of FluxPipeline configured with the loaded models.
    """
    pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16)
    pipe.enable_sequential_cpu_offload() #save some VRAM by offloading the model to CPU. Remove this if you have enough GPU power
    return pipe
