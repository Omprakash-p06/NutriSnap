"""GPU/CPU device management for NutriSnap."""

import torch
from loguru import logger


def get_device(prefer_gpu: bool = True) -> torch.device:
    """Return the best available compute device.

    Args:
        prefer_gpu: If True and CUDA is available, returns GPU device.

    Returns:
        torch.device instance.
    """
    if prefer_gpu and torch.cuda.is_available():
        device = torch.device("cuda")
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        logger.info(
            f"Using GPU: {torch.cuda.get_device_name(0)} ({vram_gb:.1f} GB VRAM)"
        )
    else:
        device = torch.device("cpu")
        logger.info("Using CPU")
    return device
