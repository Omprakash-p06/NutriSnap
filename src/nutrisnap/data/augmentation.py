"""Albumentations augmentation pipelines for NutriSnap.

Provides separate pipelines for training (heavy augmentation)
and validation/inference (minimal / resize-only).

All pipelines operate on HWC uint8 numpy arrays.
"""
import albumentations as A
import numpy as np
from albumentations.pytorch import ToTensorV2


def get_train_augmentation(image_size: int = 224) -> A.Compose:
    """Full augmentation pipeline for training.

    Applied after segmentation masking on the 224×224 preprocessed image.
    """
    return A.Compose(
        [
            # Geometric
            A.HorizontalFlip(p=0.5),
            A.Rotate(limit=30, p=0.5),
            A.RandomResizedCrop(
                size=(image_size, image_size),
                scale=(0.8, 1.0),
                ratio=(0.9, 1.1),
                p=0.5,
            ),
            # Color / lighting (pixel-level transforms that apply to BOTH)
            A.RandomBrightnessContrast(
                brightness_limit=0.2,
                contrast_limit=0.2,
                p=0.5,
            ),
            A.GaussianBlur(blur_limit=(3, 5), p=0.3),
            # OCclusion simulation
            A.CoarseDropout(
                num_holes_range=(1, 8),
                hole_height_range=(image_size // 16, image_size // 8),
                hole_width_range=(image_size // 16, image_size // 8),
                p=0.3,
            ),
        ],
        additional_targets={"depth": "image"},
    )


def get_color_augmentation() -> A.Compose:
    """Pixel-level color transforms for RGB only."""
    return A.Compose(
        [
            A.HueSaturationValue(
                hue_shift_limit=10,
                sat_shift_limit=20,
                val_shift_limit=10,
                p=0.4,
            ),
        ]
    )


def get_val_augmentation(image_size: int = 224) -> A.Compose:
    """Minimal pipeline for validation and inference (no randomness)."""
    return A.Compose(
        [A.Resize(image_size, image_size)],
        additional_targets={"depth": "image"},
    )
