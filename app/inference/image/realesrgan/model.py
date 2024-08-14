from RealESRGAN import RealESRGAN
import torch
import logging

# Setup logging
logger = logging.getLogger(__name__)

def load_realesrgan_model(scale_factor: int):
    """
    Initializes and returns a Real-ESRGAN model with the specified scale factor.
    """
    logger.info(f"Initializing Real-ESRGAN model with scale factor {scale_factor}...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    model = RealESRGAN(device, scale=scale_factor)
    model.load_weights('weights/RealESRGAN_x8.pth', download=True)
    logger.info("Real-ESRGAN model initialized and weights loaded.")
    return model