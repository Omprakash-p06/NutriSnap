"""Smoke check for the segmentation/preprocessing pipeline.

Validates generated RGBD artifacts for:
- Correct shape: (4, 224, 224)
- Correct dtype: float32
- Value ranges: RGB channels in normalized range, depth in [0, 1]
- No NaN or Inf values
- Manifest CSV consistency

Usage:
    python scripts/smoke_check_pipeline.py
    python scripts/smoke_check_pipeline.py --rgbd-dir data/processed/rgbd --limit 5
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

EXPECTED_SHAPE = (4, 224, 224)
EXPECTED_DTYPE = np.float32


def check_artifact(npy_path: Path) -> list[str]:
    """Validate a single RGBD .npy artifact.

    Returns:
        List of error messages. Empty list = all checks passed.
    """
    errors = []

    if not npy_path.exists():
        return [f"File not found: {npy_path}"]

    try:
        data = np.load(str(npy_path))
    except Exception as e:
        return [f"Failed to load {npy_path}: {e}"]

    # Shape check
    if data.shape != EXPECTED_SHAPE:
        errors.append(f"Shape mismatch: expected {EXPECTED_SHAPE}, got {data.shape}")

    # Dtype check
    if data.dtype != EXPECTED_DTYPE:
        errors.append(f"Dtype mismatch: expected {EXPECTED_DTYPE}, got {data.dtype}")

    # NaN/Inf check
    if np.isnan(data).any():
        nan_count = np.isnan(data).sum()
        errors.append(f"Contains {nan_count} NaN values")

    if np.isinf(data).any():
        inf_count = np.isinf(data).sum()
        errors.append(f"Contains {inf_count} Inf values")

    # Channel range checks
    if data.shape[0] >= 4:
        # RGB channels (0-2): ImageNet-normalized, typically in [-2.5, 3.0]
        rgb = data[:3]
        if rgb.min() < -5.0 or rgb.max() > 5.0:
            errors.append(
                f"RGB channels out of expected range: [{rgb.min():.2f}, {rgb.max():.2f}]"
            )

        # Depth channel (3): should be in [0, 1]
        depth = data[3]
        if depth.min() < -0.01 or depth.max() > 1.01:
            errors.append(
                f"Depth channel out of [0,1] range: [{depth.min():.4f}, {depth.max():.4f}]"
            )

    return errors


def check_manifest(manifest_path: Path, rgbd_dir: Path) -> list[str]:
    """Validate manifest CSV consistency."""
    errors = []

    if not manifest_path.exists():
        return [f"Manifest not found: {manifest_path}"]

    with open(manifest_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        errors.append("Manifest is empty")
        return errors

    # Check that manifest references existing files
    for row in rows:
        rgbd_p_str = row.get("rgbd_path", "")
        if not rgbd_p_str:
            errors.append("Manifest contains empty rgbd_path")
            continue
            
        rgbd_path = PROJECT_ROOT / rgbd_p_str
        if not rgbd_path.exists():
            errors.append(f"Manifest references missing file: {rgbd_p_str}")

    logger.info(f"Manifest contains {len(rows)} entries")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Smoke check segmentation pipeline output")
    parser.add_argument("--rgbd-dir", default="data/processed/rgbd", help="RGBD artifacts dir")
    parser.add_argument("--limit", type=int, default=None, help="Check only first N files")
    args = parser.parse_args()

    rgbd_dir = PROJECT_ROOT / args.rgbd_dir
    if not rgbd_dir.exists():
        logger.error(f"RGBD directory not found: {rgbd_dir}")
        logger.error("Run: python scripts/generate_rgbd_artifacts.py first")
        sys.exit(1)

    # Collect .npy files
    npy_files = sorted(rgbd_dir.glob("*.npy"))
    if not npy_files:
        logger.error(f"No .npy files found in {rgbd_dir}")
        sys.exit(1)

    if args.limit:
        npy_files = npy_files[:args.limit]

    logger.info(f"Smoke checking {len(npy_files)} RGBD artifacts in {rgbd_dir}")

    # Check artifacts
    total_errors = 0
    for i, npy_path in enumerate(npy_files):
        errors = check_artifact(npy_path)
        if errors:
            total_errors += len(errors)
            logger.error(f"[FAIL] {npy_path.name}:")
            for err in errors:
                logger.error(f"  - {err}")
        else:
            if (i + 1) % 50 == 0 or (i + 1) <= 3:
                data = np.load(str(npy_path))
                logger.info(
                    f"[PASS] {npy_path.name} — shape={data.shape} "
                    f"rgb=[{data[:3].min():.2f},{data[:3].max():.2f}] "
                    f"depth=[{data[3].min():.3f},{data[3].max():.3f}]"
                )

    # Check manifest
    manifest_path = rgbd_dir / "manifest.csv"
    manifest_errors = check_manifest(manifest_path, rgbd_dir)
    total_errors += len(manifest_errors)
    for err in manifest_errors:
        logger.error(f"[MANIFEST] {err}")

    # Summary
    logger.info("=" * 60)
    if total_errors == 0:
        logger.info(f"SMOKE CHECK PASSED — {len(npy_files)} artifacts validated ✓")
        sys.exit(0)
    else:
        logger.error(f"SMOKE CHECK FAILED — {total_errors} errors found ✗")
        sys.exit(1)


if __name__ == "__main__":
    main()
