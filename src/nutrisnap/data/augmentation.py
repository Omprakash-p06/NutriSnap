"""Albumentations augmentation pipelines with synchronized RGB/mask/depth transforms.

Ensures identical geometric transforms are applied to RGB image, segmentation mask,
and depth map simultaneously — prevents alignment shift (a common pitfall from RESEARCH.md).

Usage:
    from nutrisnap.data.augmentation import get_augmentation_pipeline

    train_aug = get_augmentation_pipeline("train", target_size=(224, 224))
    val_aug = get_augmentation_pipeline("val", target_size=(224, 224))

    # Apply to dict with "image", "mask" keys (Albumentations convention)
    result = train_aug(image=rgb, mask=food_mask)
    augmented_rgb = result["image"]
    augmented_mask = result["mask"]
"""

from typing import Optional

import albumentations as A
import numpy as np

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

# ImageNet normalization constants
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def get_augmentation_pipeline(
    mode: str = "train",
    target_size: tuple[int, int] = (224, 224),
    normalize: bool = True,
) -> A.Compose:
    """Return Albumentations Compose pipeline for train/val/test modes.

    All pipelines use `additional_targets={"depth": "image"}` so depth maps
    receive the same geometric transforms as the RGB image.

    Args:
        mode: One of "train", "val", "test".
        target_size: Output (height, width).
        normalize: Whether to add ImageNet normalization.

    Returns:
        Albumentations Compose pipeline.
    """
    target_h, target_w = target_size

    if mode == "train":
        transforms = [
            # Geometric augmentations (applied identically to image + mask + depth)
            A.HorizontalFlip(p=0.5),
            A.ShiftScaleRotate(
                shift_limit=0.05,
                scale_limit=0.1,
                rotate_limit=15,
                border_mode=0,  # cv2.BORDER_CONSTANT
                p=0.5,
            ),
            A.RandomResizedCrop(
                size=(target_h, target_w),
                scale=(0.8, 1.0),
                ratio=(0.9, 1.1),
                p=0.5,
            ),
            # Resize to target if RandomResizedCrop didn't fire
            A.Resize(height=target_h, width=target_w),
            # Color augmentations (RGB only — NOT applied to mask or depth)
            A.ColorJitter(
                brightness=0.2,
                contrast=0.2,
                saturation=0.2,
                hue=0.05,
                p=0.5,
            ),
            A.GaussNoise(std_range=(0.01, 0.03), p=0.3),
        ]
    elif mode in ("val", "test"):
        transforms = [
            A.Resize(height=target_h, width=target_w),
        ]
    else:
        raise ValueError(f"Unknown augmentation mode: {mode}. Use 'train', 'val', or 'test'.")

    # Optionally add normalization
    if normalize:
        transforms.append(
            A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD, max_pixel_value=255.0)
        )

    pipeline = A.Compose(
        transforms,
        additional_targets={"depth": "image"},
    )

    logger.debug(f"Created {mode} augmentation pipeline with {len(transforms)} transforms")
    return pipeline


def get_augmentation_pipeline_no_normalize(
    mode: str = "train",
    target_size: tuple[int, int] = (224, 224),
) -> A.Compose:
    """Convenience: pipeline without normalization (for visualization/debugging)."""
    return get_augmentation_pipeline(mode=mode, target_size=target_size, normalize=False)
