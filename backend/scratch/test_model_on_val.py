import sys
from pathlib import Path

import torch
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from nutrisnap.data.dataset import TARGET_SCALES, NutriSnapDataset
from nutrisnap.models.nutrition_regressor import get_model


def test_val_set():
    config_path = Path("configs/experiment/ensemble_mvp.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    exp_cfg = config["experiment"]
    device = "cuda" if torch.cuda.is_available() else "cpu"

    ds = NutriSnapDataset(
        features_dir=exp_cfg["features_dir"],
        split_file=Path(exp_cfg["split_dir"]) / "val_ids.txt",
        metadata_csv=exp_cfg["metadata_csv"],
        volume_features_csv=exp_cfg["volume_features_csv"],
    )

    model_cfg_path = Path(
        exp_cfg.get("model_config", "configs/models/efficientnet_v2_b0.yaml")
    )
    with open(model_cfg_path) as f:
        model_cfg = yaml.safe_load(f)

    checkpoint_dir = Path("checkpoints") / exp_cfg["name"]
    checkpoints = sorted(checkpoint_dir.glob("best_fold_*.pth"))

    for ckpt_path in checkpoints:
        print(f"\nTesting {ckpt_path.name}")
        model = get_model(model_cfg).to(device)
        ckpt = torch.load(ckpt_path, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
        model.eval()

        with torch.no_grad():
            for i in range(len(ds)):
                sample = ds[i]
                rgb = sample["rgb"].unsqueeze(0).to(device)
                depth = sample["depth"].unsqueeze(0).to(device)
                scalars = sample["scalar_features"].unsqueeze(0).to(device)

                preds = model(rgb, depth, scalars)
                preds_real = (preds[0] * TARGET_SCALES.to(device)).tolist()
                targets_real = (sample["targets"] * TARGET_SCALES).tolist()

                print(
                    f"  Dish {sample['dish_id']}: Pred={preds_real}, True={targets_real}"
                )


if __name__ == "__main__":
    test_val_set()
