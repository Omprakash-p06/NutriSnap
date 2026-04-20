#!/usr/bin/env python3
"""NutriSnap Data Preparation — single entrypoint.

Replaces the separate audit_dataset.py + generate_splits.py + generate_folds.py pipeline.
Runs all three stages in sequence:

  Stage 1 – Audit:  validates raw data (RGB, depth, nutrition row present)
  Stage 2 – Splits: 70/15/15 train/val/test split by dish_id (no leakage)
  Stage 3 – Folds:  5-fold stratified CV (stratified by calorie bins, grouped by dish_id)

Prerequisites: Run scripts/ingest_nutrition5k.py first, then this script.

Usage:
    .venv\\Scripts\\python.exe scripts/prepare_data.py              # full dataset
    .venv\\Scripts\\python.exe scripts/prepare_data.py --mvp-only  # 10-dish MVP subset
    .venv\\Scripts\\python.exe scripts/prepare_data.py --skip-audit # re-use existing dishes.csv
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Config helpers
# ──────────────────────────────────────────────────────────────────────────────


def _load_yaml(path: str | Path) -> dict:
    import yaml

    with open(path) as f:
        return yaml.safe_load(f)


def _cfg_get(cfg: dict, *keys: str, default=None):
    """Resolve a config value from either flat keys or nested under 'data:'."""
    # Try flat first (e.g. cfg["raw_dir"])
    for key in keys:
        if key in cfg:
            return cfg[key]
    # Try nested under "data:"
    data_block = cfg.get("data", {})
    for key in keys:
        if key in data_block:
            return data_block[key]
    return default


# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Audit
# ──────────────────────────────────────────────────────────────────────────────


def stage_audit(
    raw_path: Path, imagery_dir: Path, nutrition_csv: Path, ingredients_csv: Path
) -> pd.DataFrame:
    """Audit: check each dish has RGB, depth, and a nutrition row.
    Implements Phase 1.2 (Mass consistency) and Phase 1.3 (Blur detection).
    """
    logger.info("=" * 60)
    logger.info("STAGE 1 — DATA AUDIT")
    logger.info("=" * 60)

    # Load nutrition ground truth
    if not nutrition_csv.exists():
        logger.error(f"Nutrition CSV not found: {nutrition_csv}")
        sys.exit(1)

    nutrition = pd.read_csv(nutrition_csv)
    logger.info(f"  Nutrition CSV: {len(nutrition)} rows")

    # Map raw columns to internal names
    column_map = {
        "calories": "total_calories",
        "fat": "total_fat",
        "carb": "total_carb",
        "protein": "total_protein",
        "mass": "total_mass",
    }
    # Standardise column names
    if "dish_id" not in nutrition.columns:
        # Try first column
        nutrition = nutrition.rename(columns={nutrition.columns[0]: "dish_id"})

    # Rename other columns if they exist
    rename_dict = {k: v for k, v in column_map.items() if k in nutrition.columns}
    nutrition = nutrition.rename(columns=rename_dict)

    # Load ingredients for mass consistency check (Phase 1.2)
    if not ingredients_csv.exists():
        logger.error(f"Ingredients CSV not found: {ingredients_csv}")
        sys.exit(1)

    ingredients = pd.read_csv(ingredients_csv)
    # Sum grams per dish_id
    mass_sum = ingredients.groupby("dish_id")["grams"].sum().to_dict()
    logger.info(
        f"  Ingredients CSV loaded: {len(ingredients)} rows, {len(mass_sum)} dishes"
    )

    nutrition_ids = set(nutrition["dish_id"].astype(str))

    # Required columns for the audit records
    # If a column was renamed, it will be in INTERNAL_COLS; if not, use default 0.0
    INTERNAL_COLS = [
        "total_calories",
        "total_fat",
        "total_carb",
        "total_protein",
        "total_mass",
    ]

    # Scan imagery directory
    if not imagery_dir.exists():
        logger.error(f"Imagery directory not found: {imagery_dir}")
        sys.exit(1)

    dish_dirs = sorted([d for d in imagery_dir.iterdir() if d.is_dir()])
    logger.info(f"  Dish directories found: {len(dish_dirs)}")

    records = []
    missing_rgb = missing_depth = missing_nutrition = 0
    failed_mass_check = 0
    failed_blur_check = 0

    # Blur threshold (Phase 1.3)
    # Laplacian variance < 100 is generally considered blurry
    BLUR_THRESHOLD = 50

    for dish_dir in dish_dirs:
        dish_id = dish_dir.name
        has_rgb = (dish_dir / "rgb.png").exists()
        has_depth = (dish_dir / "depth_raw.png").exists()
        has_nutrition = dish_id in nutrition_ids

        if not has_rgb:
            missing_rgb += 1
        if not has_depth:
            missing_depth += 1
        if not has_nutrition:
            missing_nutrition += 1

        if has_rgb and has_nutrition:
            row = nutrition[nutrition["dish_id"].astype(str) == dish_id]
            reported_mass = float(row["total_mass"].iloc[0]) if not row.empty else 0.0
            calculated_mass = float(mass_sum.get(dish_id, 0.0))

            # Phase 1.2: Mass Consistency Check (5% threshold)
            if reported_mass > 0:
                diff = abs(reported_mass - calculated_mass) / reported_mass
                if diff > 0.05:
                    failed_mass_check += 1
                    logger.debug(
                        f"  [SKIPPED] Mass inconsistency for {dish_id}: "
                        f"rep={reported_mass:.1f}g, calc={calculated_mass:.1f}g (diff={diff:.1%})"
                    )
                    continue

            # Phase 1.3: Blur Detection (Laplacian Variance)
            rgb_path = dish_dir / "rgb.png"
            img = cv2.imread(str(rgb_path), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                variance = cv2.Laplacian(img, cv2.CV_64F).var()
                if variance < BLUR_THRESHOLD:
                    failed_blur_check += 1
                    logger.debug(
                        f"  [SKIPPED] Blurry image for {dish_id}: var={variance:.1f}"
                    )
                    continue

            record = {
                "dish_id": dish_id,
                "has_rgb": has_rgb,
                "has_depth": has_depth,
                "has_nutrition": has_nutrition,
                "rgb_path": str(rgb_path),
                "depth_path": str(dish_dir / "depth_raw.png") if has_depth else "",
            }

            # Extract macros, default to 0.0 if missing
            for col in INTERNAL_COLS:
                if col in row.columns and not row.empty:
                    record[col] = float(row[col].iloc[0])
                else:
                    record[col] = 0.0

            records.append(record)

    df = pd.DataFrame(records)
    logger.info(f"  Valid dishes:      {len(df)}")
    logger.info(f"  Missing RGB:       {missing_rgb}")
    logger.info(f"  Missing Depth:     {missing_depth}")
    logger.info(f"  Missing Nutrition: {missing_nutrition}")
    logger.info(f"  Failed Mass Check: {failed_mass_check}")
    logger.info(f"  Failed Blur Check: {failed_blur_check}")

    return df


# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Splits (70/15/15, by dish_id)
# ──────────────────────────────────────────────────────────────────────────────


def stage_splits(
    df: pd.DataFrame,
    official_test_file: Path | None,
    test_fraction: float = 0.15,
    val_fraction: float = 0.15,
    seed: int = 42,
) -> tuple[list[str], list[str], list[str]]:
    """Split dishes into train/val/test with no dish_id leakage.

    If official_test_file exists, its IDs become the test set.
    Otherwise, a random 15% is held out.
    """
    logger.info("=" * 60)
    logger.info("STAGE 2 — TRAIN / VAL / TEST SPLITS")
    logger.info("=" * 60)

    all_ids = list(df["dish_id"].unique())
    rng = np.random.default_rng(seed)

    # ── Test set ──────────────────────────────────────────────────────────────
    if official_test_file and official_test_file.exists():
        official_test_ids = set(
            l.strip() for l in official_test_file.read_text().splitlines() if l.strip()
        )
        test_ids = [d for d in all_ids if d in official_test_ids]
        trainval_ids = [d for d in all_ids if d not in official_test_ids]
        logger.info(f"  Official test split loaded: {len(test_ids)} dishes")
    else:
        n_test = max(1, int(len(all_ids) * test_fraction))
        shuffled = rng.permutation(all_ids).tolist()
        test_ids = shuffled[:n_test]
        trainval_ids = shuffled[n_test:]
        logger.info(f"  Random test split: {len(test_ids)} dishes")

    # ── Val set ───────────────────────────────────────────────────────────────
    # To get val_fraction of *total* from the train+val pool:
    adj_val = val_fraction / (1.0 - test_fraction)
    n_val = max(1, int(len(trainval_ids) * adj_val))
    shuffled_tv = rng.permutation(trainval_ids).tolist()
    val_ids = shuffled_tv[:n_val]
    train_ids = shuffled_tv[n_val:]

    logger.info(f"  Total dishes:  {len(all_ids)}")
    logger.info(
        f"  Train:         {len(train_ids)} dishes ({len(train_ids)/len(all_ids):.1%})"
    )
    logger.info(
        f"  Val:           {len(val_ids)} dishes ({len(val_ids)/len(all_ids):.1%})"
    )
    logger.info(
        f"  Test:          {len(test_ids)} dishes ({len(test_ids)/len(all_ids):.1%})"
    )

    return train_ids, val_ids, test_ids


# ──────────────────────────────────────────────────────────────────────────────
# Stage 3: 5-Fold Stratified CV
# ──────────────────────────────────────────────────────────────────────────────


def stage_folds(
    train_ids: list[str],
    df: pd.DataFrame,
    n_folds: int = 5,
    n_calorie_bins: int = 5,
    seed: int = 42,
) -> list[dict]:
    """Generate n_folds stratified by calorie bins, grouped by dish_id.

    Stratification: bin calories into n_calorie_bins quantile-based groups,
    then distribute each bin proportionally across folds. This guarantees
    each fold sees the full calorie distribution.

    Returns:
        List of dicts: [{"train": [...], "val": [...]}, ...]
    """
    logger.info("=" * 60)
    logger.info(f"STAGE 3 — {n_folds}-FOLD STRATIFIED CV")
    logger.info("=" * 60)

    # Build calorie lookup for training IDs only
    cal_map = dict(zip(df["dish_id"].astype(str), df["total_calories"]))
    train_df = pd.DataFrame(
        {
            "dish_id": train_ids,
            "calories": [cal_map.get(d, 0.0) for d in train_ids],
        }
    )

    # Quantile-based calorie bins
    train_df["calorie_bin"] = pd.qcut(
        train_df["calories"],
        q=n_calorie_bins,
        labels=False,
        duplicates="drop",
    )

    rng = np.random.default_rng(seed)
    folds: list[list[str]] = [[] for _ in range(n_folds)]

    # Distribute each bin round-robin across folds
    for bin_id in range(n_calorie_bins):
        bin_ids = train_df[train_df["calorie_bin"] == bin_id]["dish_id"].tolist()
        shuffled_bin = rng.permutation(bin_ids).tolist()
        for j, dish in enumerate(shuffled_bin):
            folds[j % n_folds].append(dish)

    # Build fold artifacts
    cv_folds = []
    for fold_idx in range(n_folds):
        val = folds[fold_idx]
        train = [d for i, fold in enumerate(folds) for d in fold if i != fold_idx]
        cv_folds.append({"fold": fold_idx, "train": train, "val": val})
        logger.info(f"  Fold {fold_idx}: train={len(train)}, val={len(val)}")

    return cv_folds


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="NutriSnap data prep: audit + splits + folds in one run"
    )
    parser.add_argument("--config", default="configs/data/data_config.yaml")
    parser.add_argument(
        "--mvp-only",
        action="store_true",
        help="Limit to MVP dish subset only (uses mvp_dish_count from config)",
    )
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="Skip audit stage (use if raw data already verified)",
    )
    parser.add_argument("--test-frac", type=float, default=0.15)
    parser.add_argument("--val-frac", type=float, default=0.15)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    cfg = _load_yaml(args.config)

    # Resolve paths from either flat or nested config layout
    raw_path = Path(
        _cfg_get(cfg, "raw_path", "raw_dir", default="data/raw/archive (4)")
    )
    imagery_sub = _cfg_get(cfg, "imagery_subdir", default="imagery/realsense_overhead")
    imagery_dir = raw_path / imagery_sub
    nutrition_csv = raw_path / "dish_nutrition_values.csv"
    splits_dir = Path(_cfg_get(cfg, "splits_dir", default="data/splits"))
    interim_dir = Path(_cfg_get(cfg, "interim_dir", default="data/interim"))
    official_test = raw_path / "dish_ids" / "splits" / "test_ids.txt"
    mvp_count = int(_cfg_get(cfg, "mvp_dish_count", default=10))

    splits_dir.mkdir(parents=True, exist_ok=True)
    interim_dir.mkdir(parents=True, exist_ok=True)

    # ── Audit ─────────────────────────────────────────────────────────────────
    if not args.skip_audit:
        ingredients_csv = raw_path / "dish_ingredients.csv"
        df = stage_audit(raw_path, imagery_dir, nutrition_csv, ingredients_csv)
    else:
        # Load pre-existing dishes.csv
        dishes_csv = interim_dir / "dishes.csv"
        if not dishes_csv.exists():
            logger.error(
                f"dishes.csv not found at {dishes_csv}. Run without --skip-audit."
            )
            sys.exit(1)
        df = pd.read_csv(dishes_csv)
        logger.info(f"[Audit skipped] Loaded {len(df)} dishes from {dishes_csv}")

    # Persist validated dish manifest
    df.to_csv(interim_dir / "dishes.csv", index=False)
    logger.info(f"  Dish manifest saved: {interim_dir / 'dishes.csv'}")

    # ── Splits ────────────────────────────────────────────────────────────────
    official_test_arg = official_test if official_test.exists() else None
    if not official_test.exists():
        logger.warning(
            f"Official test split not found at {official_test} — using random 15%"
        )

    train_ids, val_ids, test_ids = stage_splits(
        df,
        official_test_file=official_test_arg,
        test_fraction=args.test_frac,
        val_fraction=args.val_frac,
        seed=args.seed,
    )

    (splits_dir / "train_ids.txt").write_text("\n".join(train_ids) + "\n")
    (splits_dir / "val_ids.txt").write_text("\n".join(val_ids) + "\n")
    (splits_dir / "test_ids.txt").write_text("\n".join(test_ids) + "\n")
    logger.info(f"  Splits written to {splits_dir}/")

    # Also write per-fold txt files (used by train.py fallback)
    # ── Folds ─────────────────────────────────────────────────────────────────
    cv_folds = stage_folds(
        train_ids,
        df,
        n_folds=args.folds,
        seed=args.seed,
    )

    with open(splits_dir / "cv_folds.json", "w") as f:
        json.dump(cv_folds, f, indent=2)
    logger.info(f"  cv_folds.json written: {len(cv_folds)} folds")

    # Write per-fold txt files (for train.py fallback)
    for fold in cv_folds:
        i = fold["fold"]
        (splits_dir / f"train_fold_{i}.txt").write_text("\n".join(fold["train"]) + "\n")
        (splits_dir / f"val_fold_{i}.txt").write_text("\n".join(fold["val"]) + "\n")

    # ── MVP Subset (always generated; --mvp-only restricts all above to this set) ──
    # Select top N dishes by side-angle frame density (High-Density strategy)
    side_dir = raw_path / "imagery" / "side_angles"
    density_map = {}

    all_eligible = train_ids + val_ids
    for did in all_eligible:
        dpath = side_dir / did
        if dpath.exists():
            count = len(list(dpath.glob("*.jpeg")) + list(dpath.glob("*.jpg")))
            density_map[did] = count
        else:
            density_map[did] = 0

    # Sort by frame count descending
    sorted_by_density = sorted(
        all_eligible, key=lambda d: density_map.get(d, 0), reverse=True
    )
    mvp_ids = sorted_by_density[:mvp_count]

    (splits_dir / "mvp_subset_ids.txt").write_text("\n".join(mvp_ids) + "\n")
    logger.info(
        f"  MVP subset ({len(mvp_ids)} dishes) → {splits_dir}/mvp_subset_ids.txt"
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    scope = "MVP (10 dishes)" if args.mvp_only else "Full dataset"
    print(f"\n{'='*60}")
    print(f"Data preparation complete [{scope}]:")
    print(f"  Dishes validated:  {len(df)}")
    print(f"  Train:             {len(train_ids)} dishes")
    print(f"  Val:               {len(val_ids)} dishes")
    print(f"  Test:              {len(test_ids)} dishes")
    print(f"  CV folds:          {len(cv_folds)}")
    print(
        f"  MVP subset:        {len(mvp_ids)} dishes -> {splits_dir}/mvp_subset_ids.txt"
    )
    print(f"  Output:            {splits_dir}/")
    if args.mvp_only:
        print(f"\nNext step (MVP preprocessing — minutes, not hours):")
        print(
            f"  .venv\\Scripts\\python.exe scripts/preprocess_full.py --ids-file {splits_dir}\\mvp_subset_ids.txt --output-dir data/processed/features"
        )
    else:
        print(f"\nNext step:")
        print(
            f"  .venv\\Scripts\\python.exe scripts/preprocess_full.py --ids-file {splits_dir}\\train_ids.txt --output-dir data/processed/features"
        )


if __name__ == "__main__":
    main()
