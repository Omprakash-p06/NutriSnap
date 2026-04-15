#!/usr/bin/env python3
"""Master preprocessing script for NutriSnap.

Follows the SVG pre-processing steps:
1. Phase 1: Data Preparation (scripts/01_data_audit_split.py)
2. Phase 2: Segmentation (scripts/02_generate_masks.py)
3. Phase 3: RGB Preprocessing (scripts/03_rgb_preprocess.py)
4. Phase 3: Depth Preprocessing (scripts/03_depth_preprocess.py)
5. Phase 3: Feature Assembly (scripts/04_assemble_features.py)
"""
import argparse
import subprocess
import sys
from pathlib import Path

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and log progress."""
    logger.info(f"--- Running: {description} ---")
    logger.info(f"Command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, capture_output=False)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during {description}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="NutriSnap Master Preprocessing Pipeline (SVG-compliant)")
    parser.add_argument("--config", default="configs/data/data_config.yaml", help="Data config")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of dishes processed")
    parser.add_argument("--skip-audit", action="store_true", help="Skip dataset audit in Phase 1")
    args = parser.parse_args()

    common_args = ["--config", args.config]
    if args.limit:
        common_args.extend(["--limit", str(args.limit)])

    # Step 1: Phase 1: Data Preparation
    phase1_args = ["--config", args.config]
    if args.skip_audit:
        phase1_args.append("--skip-audit")
        
    if not run_command(
        [sys.executable, "scripts/01_data_audit_split.py"] + phase1_args,
        "Phase 1: Data Preparation"
    ):
        logger.error("Phase 1 failed.")
        sys.exit(1)

    # Step 2: Phase 2: Segmentation
    if not run_command(
        [sys.executable, "scripts/02_generate_masks.py"] + common_args,
        "Phase 2: Segmentation"
    ):
        logger.error("Phase 2 failed.")
        sys.exit(1)

    # Step 3: Phase 3: RGB Preprocessing
    if not run_command(
        [sys.executable, "scripts/03_rgb_preprocess.py"] + common_args,
        "Phase 3: RGB Preprocessing"
    ):
        logger.error("Phase 3 RGB Preprocessing failed.")
        sys.exit(1)

    # Step 4: Phase 3: Depth Preprocessing
    if not run_command(
        [sys.executable, "scripts/03_depth_preprocess.py"] + common_args,
        "Phase 3: Depth Preprocessing"
    ):
        logger.error("Phase 3 Depth Preprocessing failed.")
        sys.exit(1)

    # Step 5: Phase 3: Feature Assembly
    if not run_command(
        [sys.executable, "scripts/04_assemble_features.py"] + common_args,
        "Phase 3: Feature Assembly"
    ):
        logger.error("Phase 3 Feature Assembly failed.")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("PREPROCESSING PIPELINE COMPLETE (SVG-COMPLIANT)")
    logger.info(f"Data ready in data/processed/rgbd/")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
