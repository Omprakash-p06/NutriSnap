import sys
from pathlib import Path

import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nutrisnap.models.loss import UncertaintyWeightedLoss  # noqa: E402
from nutrisnap.models.nutrition_regressor import NutritionRegressor  # noqa: E402
from nutrisnap.training.trainer import NutritionTrainer  # noqa: E402


def diagnose():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"CUDA Available: {torch.cuda.is_available()}")
    print(f"Target Device: {device}")

    model = NutritionRegressor(backbone_name="efficientnet_v2_b0", pretrained=False)
    criterion = UncertaintyWeightedLoss()

    trainer = NutritionTrainer(model=model, criterion=criterion, device=device)

    print(f"Model internal device: {next(model.parameters()).device}")
    print(f"Trainer device property: {trainer.device}")

    # Check if GPU memory is actually being allocated
    if "cuda" in str(next(model.parameters()).device):
        print(f"GPU Memory Allocated: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
        print(f"GPU Memory Reserved: {torch.cuda.memory_reserved() / 1024**2:.2f} MB")
    else:
        print("Model is NOT on GPU!")


if __name__ == "__main__":
    diagnose()
