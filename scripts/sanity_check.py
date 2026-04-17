import torch
import yaml
from pathlib import Path
from torch.utils.data import DataLoader
import logging
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nutrisnap.data.dataset import NutriSnapDataset
from nutrisnap.models.nutrition_regressor import get_model
from nutrisnap.training.trainer import NutritionTrainer

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def run_sanity_checks(config_path):
    logger.info(f"Starting sanity checks with config: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)['experiment']
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # 1. Load Data (One batch)
    try:
        # Load the first fold's training split
        split_path = Path(config['split_dir']) / "_tmp_train_fold_0.txt"
        dataset = NutriSnapDataset(
            features_dir=config['features_dir'],
            split_file=split_path,
            metadata_csv=config['metadata_csv']
        )
        loader = DataLoader(dataset, batch_size=8, shuffle=True)
        batch = next(iter(loader))
        logger.info("✅ Data loading check passed")
    except Exception as e:
        logger.error(f"❌ Data loading failed: {e}")
        return

    # Move batch to device
    batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}

    # 2. Forward Pass
    try:
        # Correctly load the model config YAML
        model_cfg_path = Path(config['model_config'])
        if not model_cfg_path.is_absolute():
            model_cfg_path = Path(__file__).resolve().parent.parent / model_cfg_path
            
        with open(model_cfg_path, 'r') as f:
            model_cfg = yaml.safe_load(f)
            
        model = get_model(model_cfg).to(device)
        model.train()
        preds = model(batch['rgb'], batch['depth'], batch['scalar_features'])
        
        if preds.shape == (8, 4) and not torch.isnan(preds).any():
            logger.info(f"✅ Forward pass check passed (Shape: {preds.shape})")
        else:
            logger.error(f"❌ Forward pass failed. Shape: {preds.shape}, NaN found: {torch.isnan(preds).any()}")
            return
    except Exception as e:
        logger.error(f"❌ Forward pass crashed: {e}")
        return

    # 3. Backward Pass (Gradient Flow)
    try:
        criterion = torch.nn.HuberLoss()
        loss = criterion(preds, batch['targets'])
        loss.backward()
        
        has_grads = True
        for name, param in model.named_parameters():
            if param.requires_grad and param.grad is None:
                logger.error(f"❌ Parameter {name} has NO gradient!")
                has_grads = False
        
        if has_grads:
            logger.info("✅ Backward pass check passed (all parameters have gradients)")
        else:
            return
    except Exception as e:
        logger.error(f"❌ Backward pass crashed: {e}")
        return

    # 4. Overfit One Batch
    logger.info("Starting 'Overfit One Batch' test (100 iterations)...")
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    initial_loss = loss.item()
    last_loss = initial_loss
    
    for i in range(100):
        optimizer.zero_grad()
        out = model(batch['rgb'], batch['depth'], batch['scalar_features'])
        l = criterion(out, batch['targets'])
        l.backward()
        optimizer.step()
        last_loss = l.item()
        
        if (i+1) % 20 == 0:
            logger.info(f"  Iteration {i+1}/100 | Loss: {last_loss:.6f}")

    if last_loss < initial_loss * 0.1:
        logger.info(f"✅ Overfit check passed (Initial: {initial_loss:.4f} -> Final: {last_loss:.4f})")
    else:
        logger.warning(f"⚠️ Overfit check inconclusive (Initial: {initial_loss:.4f} -> Final: {last_loss:.4f})")

    logger.info("ALL SANITY CHECKS COMPLETED")

if __name__ == "__main__":
    config_file = "configs/experiment/ensemble_mvp.yaml"
    run_sanity_checks(config_file)
