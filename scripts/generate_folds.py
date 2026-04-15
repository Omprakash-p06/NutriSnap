"""Generate 5-fold cross-validation split files from the training set.

Usage:
    python scripts/generate_folds.py --config configs/data/data_config.yaml
"""
import argparse
import random
from pathlib import Path

from nutrisnap.utils.config_loader import load_data_config
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Generate 5-fold splits")
    parser.add_argument("--config", default="configs/data/data_config.yaml")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    # Load data config
    data_cfg = load_data_config(args.config)
    split_dir = Path(data_cfg.splits_dir)
    train_file = split_dir / "train_ids.txt"

    if not train_file.exists():
        logger.error(f"Train IDs not found: {train_file}")
        return

    # Load all training IDs
    ids = train_file.read_text().splitlines()
    ids = [i.strip() for i in ids if i.strip()]
    
    random.seed(args.seed)
    random.shuffle(ids)

    n = len(ids)
    fold_size = n // args.folds
    
    logger.info(f"Generating {args.folds} folds from {n} training samples...")

    for i in range(args.folds):
        val_start = i * fold_size
        val_end = (i + 1) * fold_size if i < args.folds - 1 else n
        
        val_ids = ids[val_start:val_end]
        train_ids = ids[:val_start] + ids[val_end:]
        
        train_out = split_dir / f"train_fold_{i}.txt"
        val_out = split_dir / f"val_fold_{i}.txt"
        
        train_out.write_text("\n".join(train_ids))
        val_out.write_text("\n".join(val_ids))
        
        logger.info(f"Fold {i}: Train={len(train_ids)}, Val={len(val_ids)}")

    logger.info("Fold generation complete.")


if __name__ == "__main__":
    main()
