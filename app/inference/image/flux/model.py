import os
import torch
from diffusers import FluxTransformer2DModel, FluxPipeline
from transformers import T5EncoderModel
from optimum.quanto import freeze, qfloat8, quantize
from PIL import Image as PIL
import logging
import random

class FluxPipelineManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FluxPipelineManager, cls).__new__(cls)
            cls._instance.logger = logging.getLogger()
            cls._instance.logger.setLevel(logging.INFO)
            cls._instance.pipe = None
            cls._instance.transformer = None
            cls._instance.text_encoder_2 = None
            cls._instance._initialize_pipeline()  # Initialize the pipeline only once when instance is created
        return cls._instance

    def clear_cuda_memory(self):
        torch.cuda.empty_cache()
        self.logger.info("CUDA memory cleared.")

    def _initialize_pipeline(self):
        """Internal method to initialize the pipeline once."""
        flux_version = os.getenv("FLUX_VERSION", "default_version")
        self.logger.info(f"FLUX_VERSION environment variable is set to: {flux_version}")
        if flux_version == "schnell":
            self._initialize_schnell_pipeline()
        else:
            self._initialize_default_pipeline()

    def _initialize_schnell_pipeline(self):
        """Initialize the 'schnell' version of the pipeline."""
        if self.pipe is None:
            self.logger.info("Initializing Schnell model pipeline.")
            self.pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16)
            self.logger.info("Schnell model pipeline loaded successfully.")
            self.pipe.enable_sequential_cpu_offload()
            self.logger.info("Sequential CPU offload enabled for Schnell pipeline.")
            self.pipe.vae.enable_slicing()
            self.logger.info("VAE slicing enabled for Schnell pipeline.")
            self.pipe.vae.enable_tiling()
            self.logger.info("VAE tiling enabled for Schnell pipeline.")
        else:
            self.logger.info("Schnell pipeline is already initialized.")

    def _initialize_default_pipeline(self):
        """Initialize the default version of the pipeline."""
        if self.pipe is None:
            self.logger.info("Initializing FluxTransformer2DModel and text encoder for default pipeline.")
            bfl_repo = "black-forest-labs/FLUX.1-dev"
            dtype = torch.bfloat16

            # Load and configure transformer model
            self.transformer = FluxTransformer2DModel.from_single_file(
                "https://huggingface.co/Kijai/flux-fp8/blob/main/flux1-dev-fp8.safetensors", 
                torch_dtype=dtype
            )
            self.logger.info("FluxTransformer2DModel loaded from single file.")
            quantize(self.transformer, weights=qfloat8)
            self.logger.info("Quantization applied to transformer model.")
            freeze(self.transformer)
            self.logger.info("Transformer model weights frozen.")

            # Load and configure text encoder
            self.text_encoder_2 = T5EncoderModel.from_pretrained(
                bfl_repo, 
                subfolder="text_encoder_2", 
                torch_dtype=dtype
            )
            self.logger.info("T5EncoderModel loaded from pre-trained repository.")
            quantize(self.text_encoder_2, weights=qfloat8)
            self.logger.info("Quantization applied to text encoder.")
            freeze(self.text_encoder_2)
            self.logger.info("Text encoder weights frozen.")

            # Initialize the FluxPipeline
            self.pipe = FluxPipeline.from_pretrained(bfl_repo, transformer=None, text_encoder_2=None, torch_dtype=dtype)
            self.pipe.transformer = self.transformer
            self.pipe.text_encoder_2 = self.text_encoder_2
            self.logger.info("FluxPipeline initialized with custom transformer and text encoder.")
            self.pipe.enable_model_cpu_offload()
            self.logger.info("Model CPU offload enabled for default pipeline.")
        else:
            self.logger.info("Default pipeline is already initialized.")

    def generate_image(self, prompt: str, initial_width: int, initial_height: int) -> PIL:
        """Generates an image using the pre-loaded pipeline."""
        self.logger.info(f"Generating image with prompt: '{prompt}' and dimensions: '{initial_width}x{initial_height}'")
        image = self.pipe(
            prompt=prompt,
            guidance_scale=100,
            height=initial_height,
            max_sequence_length=255,
            width=initial_width,
            num_inference_steps=16,
            generator=torch.Generator("cpu").manual_seed(random.randint(1, 123456))
        ).images[0]
        self.logger.info("Image generated successfully.")
        return image
