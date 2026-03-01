"""Image Preprocessing and Augmentation Script.

Preprocessing pipeline for training data preparation.
"""

import os
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np


class ImagePreprocessor:
    """Image preprocessing and augmentation for training.

    Attributes:
        target_size: Target image dimension.
    """

    def __init__(self, target_size: int = 640) -> None:
        """Initialize preprocessor.

        Args:
            target_size: Target image dimension.
        """
        self.target_size = target_size

    def resize(self, image: np.ndarray) -> np.ndarray:
        """Resize image to target size."""
        return cv2.resize(
            image,
            (self.target_size, self.target_size),
            interpolation=cv2.INTER_LINEAR,
        )

    def apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """Apply CLAHE for contrast enhancement."""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l_channel)

        lab_enhanced = cv2.merge([l_enhanced, a, b])
        return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    def white_balance(self, image: np.ndarray) -> np.ndarray:
        """Apply gray-world white balance."""
        result = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
        avg_a = np.average(result[:, :, 1])
        avg_b = np.average(result[:, :, 2])

        result[:, :, 1] = result[:, :, 1] - (
            (avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1
        )
        result[:, :, 2] = result[:, :, 2] - (
            (avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1
        )

        result = np.clip(result, 0, 255).astype(np.uint8)
        return cv2.cvtColor(result, cv2.COLOR_LAB2BGR)

    def denoise(self, image: np.ndarray) -> np.ndarray:
        """Apply noise reduction."""
        return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

    def sharpen(self, image: np.ndarray) -> np.ndarray:
        """Apply unsharp masking."""
        gaussian = cv2.GaussianBlur(image, (0, 0), 3)
        return cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Full preprocessing pipeline."""
        processed = self.resize(image)
        processed = self.apply_clahe(processed)
        processed = self.white_balance(processed)
        return processed


class DataAugmentor:
    """Data augmentation for training images.

    Attributes:
        target_size: Target image dimension.
    """

    def __init__(self, target_size: int = 640) -> None:
        """Initialize augmentor.

        Args:
            target_size: Target image dimension.
        """
        self.target_size = target_size

    def rotate(
        self,
        image: np.ndarray,
        angle: float = 15.0,
    ) -> np.ndarray:
        """Rotate image by random angle."""
        angle = np.random.uniform(-angle, angle)
        center = (self.target_size // 2, self.target_size // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(
            image,
            matrix,
            (self.target_size, self.target_size),
            borderMode=cv2.BORDER_REFLECT,
        )

    def flip_horizontal(self, image: np.ndarray) -> np.ndarray:
        """Flip image horizontally."""
        return cv2.flip(image, 1)

    def adjust_brightness(
        self,
        image: np.ndarray,
        factor_range: Tuple[float, float] = (0.7, 1.3),
    ) -> np.ndarray:
        """Adjust image brightness."""
        factor = np.random.uniform(*factor_range)
        return np.clip(image * factor, 0, 255).astype(np.uint8)

    def adjust_contrast(
        self,
        image: np.ndarray,
        factor_range: Tuple[float, float] = (0.7, 1.3),
    ) -> np.ndarray:
        """Adjust image contrast."""
        factor = np.random.uniform(*factor_range)
        mean = np.mean(image)
        return np.clip((image - mean) * factor + mean, 0, 255).astype(np.uint8)

    def color_jitter(self, image: np.ndarray) -> np.ndarray:
        """Apply random color jittering."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)

        # Hue shift
        hsv[:, :, 0] = (hsv[:, :, 0] + np.random.uniform(-10, 10)) % 180

        # Saturation
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * np.random.uniform(0.7, 1.3), 0, 255)

        # Value
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * np.random.uniform(0.7, 1.3), 0, 255)

        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    def augment(
        self,
        image: np.ndarray,
        n_augmentations: int = 5,
    ) -> List[np.ndarray]:
        """Generate multiple augmented versions of an image.

        Args:
            image: Input image.
            n_augmentations: Number of augmented copies.

        Returns:
            List of augmented images.
        """
        augmented = [image]  # Include original

        for _ in range(n_augmentations):
            aug = image.copy()

            # Randomly apply augmentations
            if np.random.random() > 0.5:
                aug = self.rotate(aug)

            if np.random.random() > 0.5:
                aug = self.flip_horizontal(aug)

            if np.random.random() > 0.5:
                aug = self.adjust_brightness(aug)

            if np.random.random() > 0.5:
                aug = self.adjust_contrast(aug)

            if np.random.random() > 0.5:
                aug = self.color_jitter(aug)

            augmented.append(aug)

        return augmented


def process_dataset(
    input_dir: str = "./ml/data/raw/",
    output_dir: str = "./ml/data/processed/",
    augment: bool = True,
    n_augmentations: int = 3,
) -> None:
    """Process entire dataset with preprocessing and augmentation.

    Args:
        input_dir: Directory containing raw images.
        output_dir: Directory to save processed images.
        augment: Whether to apply augmentation.
        n_augmentations: Number of augmented copies per image.
    """
    preprocessor = ImagePreprocessor()
    augmentor = DataAugmentor()

    os.makedirs(output_dir, exist_ok=True)

    # Get all images
    image_extensions = {".jpg", ".jpeg", ".png"}
    image_files = [
        f for f in Path(input_dir).glob("**/*") if f.suffix.lower() in image_extensions
    ]

    print(f"Found {len(image_files)} images")

    total_output = 0
    for img_path in image_files:
        print(f"Processing: {img_path.name}")

        # Load image
        image = cv2.imread(str(img_path))
        if image is None:
            print(f"  Error loading image, skipping")
            continue

        # Preprocess
        processed = preprocessor.preprocess(image)

        # Save preprocessed
        output_path = Path(output_dir) / img_path.name
        cv2.imwrite(str(output_path), processed)
        total_output += 1

        # Augment if enabled
        if augment:
            augmented = augmentor.augment(processed, n_augmentations)

            for i, aug in enumerate(augmented[1:], 1):  # Skip original
                aug_path = Path(output_dir) / f"{img_path.stem}_aug{i}{img_path.suffix}"
                cv2.imwrite(str(aug_path), aug)
                total_output += 1

    print(f"\nProcessed {len(image_files)} images")
    print(f"Total output images: {total_output}")
    print(f"Saved to: {output_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess and augment images")
    parser.add_argument("--input", default="./ml/data/raw/", help="Input directory")
    parser.add_argument(
        "--output", default="./ml/data/processed/", help="Output directory"
    )
    parser.add_argument(
        "--no-augment", action="store_true", help="Disable augmentation"
    )
    parser.add_argument("--n-aug", type=int, default=3, help="Augmentations per image")

    args = parser.parse_args()

    process_dataset(
        input_dir=args.input,
        output_dir=args.output,
        augment=not args.no_augment,
        n_augmentations=args.n_aug,
    )
