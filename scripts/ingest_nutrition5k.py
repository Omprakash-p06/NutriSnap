#!/usr/bin/env python3
"""Nutrition5k ingestion script.

Loads dish_nutrition_values.csv, validates schema, and writes
a normalized interim/dishes.csv for downstream use.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add src/ to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from nutrisnap.utils.config_loader import load_data_config
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

RAW_TO_INTERNAL = {
    "dish_id": "dish_id",
    "calories": "total_calories",
    "fat": "total_fat",
    "carb": "total_carb",
    "protein": "total_protein",
    "mass": "total_mass",
}


def ingest(config_path: str) -> None:
    cfg = load_data_config(config_path)
    raw_dir = Path(cfg.raw_dir)
    interim_dir = Path(cfg.interim_dir)
    interim_dir.mkdir(parents=True, exist_ok=True)

    nutrition_csv = raw_dir / "dish_nutrition_values.csv"
    if not nutrition_csv.exists():
        logger.error(f"dish_nutrition_values.csv not found at {nutrition_csv}")
        sys.exit(1)

    df = pd.read_csv(nutrition_csv)
    logger.info(f"Loaded {len(df)} rows, {df['dish_id'].nunique()} unique dishes")

    # Map columns
    # Find intersection of RAW_TO_INTERNAL keys and actual columns
    actual_cols = df.columns.tolist()
    column_map = {k: v for k, v in RAW_TO_INTERNAL.items() if k in actual_cols}

    df = df.rename(columns=column_map)

    # Keep only one row per dish_id (the summary row, not ingredient-level rows)
    # In Nutrition5k, the summary row has all macros populated.
    # Filter to rows where total_calories > 0
    summary_df = df[df["total_calories"] > 0].drop_duplicates(subset=["dish_id"])
    logger.info(f"After dedup: {len(summary_df)} unique dish summaries")

    # Define internal canonical columns
    INTERNAL_COLS = [
        "dish_id",
        "total_calories",
        "total_fat",
        "total_carb",
        "total_protein",
        "total_mass",
    ]

    # Write normalized interim CSV
    out_path = interim_dir / "dishes.csv"
    summary_df[INTERNAL_COLS].to_csv(out_path, index=False)
    logger.info(f"Wrote {len(summary_df)} dish summaries to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Ingest Nutrition5k dataset")
    parser.add_argument("--config", default="configs/data/data_config.yaml")
    args = parser.parse_args()
    ingest(args.config)


if __name__ == "__main__":
    main()
