#!/usr/bin/env python3
"""Split generation script.

Generates leakage-safe train/val/test splits and 5-fold CV artifacts
from the ingested dishes.csv. Selects MVP dish subset.

Prerequisite: Run scripts/ingest_nutrition5k.py first.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# Add src/ to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from nutrisnap.utils.config_loader import load_data_config
from nutrisnap.utils.logger import get_logger
from nutrisnap.data.splitter import (
    generate_train_test_split,
    generate_val_split,
    generate_cv_folds,
    select_mvp_subset,
)

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Generate NutriSnap dataset splits")
    parser.add_argument("--config", default="configs/data/data_config.yaml")
    args = parser.parse_args()

    cfg = load_data_config(args.config)
    interim_dir = Path(cfg.interim_dir)
    splits_dir = Path(cfg.splits_dir)
    splits_dir.mkdir(parents=True, exist_ok=True)

    # Load ingested dishes
    dishes_csv = interim_dir / "dishes.csv"
    if not dishes_csv.exists():
        logger.error(f"dishes.csv not found at {dishes_csv}. Run ingest_nutrition5k.py first.")
        sys.exit(1)

    df = pd.read_csv(dishes_csv)
    logger.info(f"Loaded {len(df)} dish summaries for split generation")

    # Step 1: Train+Val / Test split (85/15 by default)
    logger.info("=== Step 1: Train+Val / Test Split ===")
    all_train_ids, test_ids = generate_train_test_split(df, cfg, test_fraction=cfg.test_fraction)

    # Step 2: Carve validation from (Train+Val)
    # To get 15% of total from 85% of total, we need 15/85 ~= 0.176 fraction of the remainder
    adj_val_fraction = cfg.val_fraction / (1.0 - cfg.test_fraction)
    logger.info(f"=== Step 2: Validation Split (adjusted fraction: {adj_val_fraction:.4f}) ===")
    
    # Temporarily override cfg.val_fraction for the call
    original_val_frac = cfg.val_fraction
    cfg.val_fraction = adj_val_fraction
    final_train_ids, val_ids = generate_val_split(all_train_ids, df, cfg)
    cfg.val_fraction = original_val_frac

    # Step 3: 5-fold CV on training set
    logger.info("=== Step 3: 5-Fold CV Artifacts ===")
    cv_artifact = generate_cv_folds(final_train_ids, df, cfg)

    # Step 4: MVP subset selection
    logger.info("=== Step 4: MVP Subset Selection ===")
    mvp_ids, mvp_artifact = select_mvp_subset(final_train_ids, df, cfg)

    # Persistence
    logger.info(f"=== Step 5: Persistence to {splits_dir} ===")
    (splits_dir / "train_ids.txt").write_text("\n".join(final_train_ids) + "\n")
    (splits_dir / "val_ids.txt").write_text("\n".join(val_ids) + "\n")
    (splits_dir / "test_ids.txt").write_text("\n".join(test_ids) + "\n")
    (splits_dir / "mvp_subset_ids.txt").write_text("\n".join(mvp_ids) + "\n")

    with open(splits_dir / "cv_folds.json", "w") as f:
        json.dump(cv_artifact, f, indent=2)

    with open(Path("configs/data/selected_dishes.json"), "w") as f:
        json.dump(mvp_artifact, f, indent=2)

    # Summary
    print(f"\n{'='*50}")
    print(f"Split generation complete:")
    print(f"  Train: {len(final_train_ids)} dishes -> {splits_dir}/train_ids.txt")
    print(f"  Val:   {len(val_ids)} dishes -> {splits_dir}/val_ids.txt")
    print(f"  Test:  {len(test_ids)} dishes -> {splits_dir}/test_ids.txt")
    print(f"  CV:    {cfg.n_cv_folds} folds -> {splits_dir}/cv_folds.json")
    print(f"  MVP:   {len(mvp_ids)} dishes -> {splits_dir}/mvp_subset_ids.txt")
    print(f"         Selected dish IDs: {mvp_ids}")


if __name__ == "__main__":
    main()
