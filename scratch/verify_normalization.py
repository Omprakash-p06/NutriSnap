import torch
from pathlib import Path
import yaml
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from nutrisnap.data.dataset import NutriSnapDataset, collate_fn

def test_dataset_normalization():
    config_path = Path("configs/experiment/ensemble_mvp.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    exp_cfg = config["experiment"]
    
    ds = NutriSnapDataset(
        features_dir=exp_cfg["features_dir"],
        split_file=Path(exp_cfg["split_dir"]) / "val_ids.txt",
        metadata_csv=exp_cfg["metadata_csv"],
        volume_features_csv=exp_cfg["volume_features_csv"]
    )
    
    if len(ds) == 0:
        print("Dataset is empty!")
        return
        
    sample = ds[0]
    scalar_features = sample["scalar_features"]
    print(f"Sample dish_id: {sample['dish_id']}")
    print(f"Normalized Scalar features: {scalar_features}")
    
    # Check if they are in expected range roughly [0, 2]
    # Based on cat data/processed/features/volume_features.csv
    # dish_1556575558,1492.479,241.289,1.0
    # Expected: [1.492, 1.206, 1.0]
    
    if torch.any(scalar_features > 5.0):
         print("Warning: Some scalar features are still large!")
    else:
         print("Scalar features look correctly normalized.")

if __name__ == "__main__":
    test_dataset_normalization()
