"""Leakage-safe dataset splitting for NutriSnap.

All splits are grouped by dish_id to prevent scan-level leakage across boundaries.
Stratification uses calorie bins to maintain distribution balance across folds.
"""

from datetime import datetime

import numpy as np
import pandas as pd
from nutrisnap.utils.config_loader import DataConfig
from nutrisnap.utils.logger import get_logger
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold

logger = get_logger(__name__)


def _assign_calorie_bins(df: pd.DataFrame, bins: list[int]) -> np.ndarray:
    """Assign calorie bin labels for stratification."""
    labels = pd.cut(df["total_calories"], bins=bins, labels=False, right=True)
    # Fill any out-of-range values with the highest bin
    labels = labels.fillna(len(bins) - 2).astype(int)
    return labels.values


def generate_train_test_split(
    df: pd.DataFrame,
    cfg: DataConfig,
    test_fraction: float = 0.15,
) -> tuple[list[str], list[str]]:
    """Generate leakage-safe train/test split from dish_nutrition_values dataframe.

    Groups by dish_id and stratifies by calorie bins.

    Args:
        df: DataFrame with dish_id and total_calories columns.
        cfg: DataConfig with random_seed and calorie_bins.
        test_fraction: Fraction of dishes for test set.

    Returns:
        (train_ids, test_ids) lists of dish_id strings.
    """
    dish_ids = df["dish_id"].values
    calorie_bins = _assign_calorie_bins(df, cfg.calorie_bins)

    gss = GroupShuffleSplit(
        n_splits=1, test_size=test_fraction, random_state=cfg.random_seed
    )
    train_idx, test_idx = next(
        gss.split(np.zeros(len(df)), calorie_bins, groups=dish_ids)
    )

    train_ids = df.iloc[train_idx]["dish_id"].tolist()
    test_ids = df.iloc[test_idx]["dish_id"].tolist()

    # Validate no leakage
    overlap = set(train_ids) & set(test_ids)
    if overlap:
        raise ValueError(
            f"LEAKAGE DETECTED: {len(overlap)} dish_ids appear in both train and test splits!"
        )

    logger.info(f"Train: {len(train_ids)} dishes | Test: {len(test_ids)} dishes")

    return train_ids, test_ids


def generate_val_split(
    train_ids: list[str],
    df: pd.DataFrame,
    cfg: DataConfig,
) -> tuple[list[str], list[str]]:
    """Carve a validation split from train_ids using GroupShuffleSplit.

    Returns (remaining_train_ids, val_ids).
    """
    train_df = df[df["dish_id"].isin(train_ids)].copy()
    dish_ids = train_df["dish_id"].values
    calorie_bins = _assign_calorie_bins(train_df, cfg.calorie_bins)

    gss = GroupShuffleSplit(
        n_splits=1, test_size=cfg.val_fraction, random_state=cfg.random_seed + 1
    )
    remaining_idx, val_idx = next(
        gss.split(np.zeros(len(train_df)), calorie_bins, groups=dish_ids)
    )

    remaining_train_ids = train_df.iloc[remaining_idx]["dish_id"].tolist()
    val_ids = train_df.iloc[val_idx]["dish_id"].tolist()

    # Validate
    overlap = set(remaining_train_ids) & set(val_ids)
    if overlap:
        raise ValueError(f"LEAKAGE: {len(overlap)} dish_ids in both train and val!")

    logger.info(
        f"Train (after val split): {len(remaining_train_ids)} | Val: {len(val_ids)}"
    )

    return remaining_train_ids, val_ids


def generate_cv_folds(
    train_ids: list[str],
    df: pd.DataFrame,
    cfg: DataConfig,
) -> dict:
    """Generate 5-fold CV artifacts with StratifiedGroupKFold.

    Returns:
        Fold artifact dict with n_folds, created, random_seed, folds.
    """
    train_df = df[df["dish_id"].isin(train_ids)].copy()
    dish_ids = train_df["dish_id"].values
    calorie_bins = _assign_calorie_bins(train_df, cfg.calorie_bins)

    sgkf = StratifiedGroupKFold(
        n_splits=cfg.n_cv_folds, shuffle=True, random_state=cfg.random_seed
    )
    folds = []
    for fold_id, (tr_idx, val_idx) in enumerate(
        sgkf.split(np.zeros(len(train_df)), calorie_bins, groups=dish_ids)
    ):
        fold_train = train_df.iloc[tr_idx]["dish_id"].tolist()
        fold_val = train_df.iloc[val_idx]["dish_id"].tolist()

        # Validate no leakage within fold
        overlap = set(fold_train) & set(fold_val)
        if overlap:
            raise ValueError(
                f"LEAKAGE in fold {fold_id}: {len(overlap)} dishes in both train and val!"
            )

        folds.append({"fold_id": fold_id, "train_ids": fold_train, "val_ids": fold_val})
        logger.info(f"Fold {fold_id}: {len(fold_train)} train | {len(fold_val)} val")

    artifact = {
        "n_folds": cfg.n_cv_folds,
        "created": datetime.now().date().isoformat(),
        "random_seed": cfg.random_seed,
        "stratification": "calorie_bins",
        "grouping": "dish_id",
        "calorie_bins": cfg.calorie_bins,
        "folds": folds,
    }

    return artifact


def select_mvp_subset(
    train_ids: list[str],
    df: pd.DataFrame,
    cfg: DataConfig,
) -> tuple[list[str], dict]:
    """Select a 5-10 dish MVP subset from train_ids that spans the calorie range.

    Selection strategy: bin the calorie range into n_dishes equal quantile groups
    and pick one representative dish from each bin to maximize variety and spread.

    Returns:
        (selected_ids, subset_artifact)
    """
    train_df = df[df["dish_id"].isin(train_ids)].copy().reset_index(drop=True)
    n = cfg.mvp_dish_count

    # Sort by calories and split into n quantile groups
    train_df = train_df.sort_values("total_calories").reset_index(drop=True)
    group_size = max(1, len(train_df) // n)

    selected = []
    for i in range(n):
        start = i * group_size
        end = min(start + group_size, len(train_df))
        if start >= len(train_df):
            break
        group = train_df.iloc[start:end]
        # Pick the median dish from each group
        middle_idx = len(group) // 2
        row = group.iloc[middle_idx]
        selected.append(
            {
                "dish_id": row["dish_id"],
                "total_calories": float(row["total_calories"]),
                "total_fat": float(row.get("total_fat", 0)),
                "total_carb": float(row.get("total_carb", 0)),
                "total_protein": float(row.get("total_protein", 0)),
            }
        )

    selected_ids = [s["dish_id"] for s in selected]
    logger.info(
        f"Selected {len(selected_ids)} MVP dishes covering ~{train_df['total_calories'].min():.0f}–{train_df['total_calories'].max():.0f} kcal range"
    )

    subset_artifact = {
        "n_dishes": len(selected),
        "dish_ids": selected_ids,
        "selection_criteria": "calorie quantile spread — one dish per calorie quantile group",
        "dishes": selected,
        "created": datetime.now().date().isoformat(),
    }

    return selected_ids, subset_artifact
