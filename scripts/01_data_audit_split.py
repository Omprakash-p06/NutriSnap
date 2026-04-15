#!/usr/bin/env python3
"""Phase 1: Data Preparation script.

Combines dataset audit, ingestion, and split generation.
Follows the NutriSnap pre-processing pipeline Step 1.
"""
import argparse
import sys
import subprocess
from pathlib import Path

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

def run_script(script_path: str, args: list[str], description: str) -> bool:
    """Run a script and log progress."""
    logger.info(f"--- Running: {description} ({script_path}) ---")
    cmd = [sys.executable, script_path] + args
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during {description}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Phase 1: Data Audit and Split Generation")
    parser.add_argument("--config", default="configs/data/data_config.yaml", help="Data config")
    parser.add_argument("--skip-audit", action="store_true", help="Skip dataset audit")
    args = parser.parse_args()

    # 1. Audit
    if not args.skip_audit:
        if not run_script("scripts/audit_dataset.py", ["--config", args.config], "Dataset Audit"):
            sys.exit(1)
    
    # 2. Ingest
    if not run_script("scripts/ingest_nutrition5k.py", ["--config", args.config], "Data Ingestion"):
        sys.exit(1)
        
    # 3. Splits
    if not run_script("scripts/generate_splits.py", ["--config", args.config], "Split Generation"):
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("PHASE 1 COMPLETE: Data Audited and Splits Generated")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
