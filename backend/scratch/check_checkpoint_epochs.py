from pathlib import Path

import torch


def check_epochs():
    checkpoint_dir = Path("checkpoints/ensemble_mvp_v1")
    checkpoints = sorted(checkpoint_dir.glob("best_fold_*.pth"))

    for ckpt_path in checkpoints:
        ckpt = torch.load(ckpt_path, map_location="cpu")
        print(
            f"{ckpt_path.name}: Best Epoch = {ckpt['epoch']}, Val Loss = {ckpt['val_loss']:.4f}"
        )


if __name__ == "__main__":
    check_epochs()
