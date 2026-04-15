#!/usr/bin/env python3
"""Nutrition5k dataset audit script.

Verifies dataset integrity: dish IDs, imagery presence, annotation completeness.
Exits 0 if all checks pass (or only warnings). Exits 1 if critical issues found.
Writes reports/audit_report.json with results.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
from PIL import Image

# Add src/ to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from nutrisnap.utils.config_loader import load_data_config
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

REQUIRED_MACRO_COLS = ["calories", "fat", "carb", "protein", "mass"]


def check_imagery(dish_id: str, imagery_dir: Path) -> tuple[bool, str]:
    """Check if at least one valid overhead RGB image exists for a dish_id."""
    # Search realsense_overhead directory
    realsense_dir = imagery_dir / "realsense_overhead"
    if not realsense_dir.exists():
        return False, f"realsense_overhead/ directory missing"

    # Look for dish folder or matching images
    dish_images = list(realsense_dir.glob(f"{dish_id}*"))
    if not dish_images:
        # Also try subdirectory pattern
        dish_dir = realsense_dir / dish_id
        if dish_dir.exists():
            dish_images = list(dish_dir.glob("*.jpg")) + list(dish_dir.glob("*.png"))

    if not dish_images:
        return False, f"No imagery found for {dish_id}"

    return True, "OK"


def verify_image(path: Path) -> tuple[bool, str]:
    """Check image file for corruption using PIL verify."""
    try:
        with Image.open(path) as img:
            img.verify()
        return True, "OK"
    except Exception as e:
        return False, str(e)


def audit_dataset(config_path: str) -> dict:
    """Run full dataset audit.

    Returns:
        Audit report dict. Sets 'critical_issues' key if any blockers found.
    """
    cfg = load_data_config(config_path)
    raw_dir = Path(cfg.raw_dir)
    imagery_dir = raw_dir / "imagery"
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "audit_date": datetime.now().isoformat(),
        "raw_dir": str(raw_dir),
        "total_dishes": 0,
        "dishes_with_missing_imagery": [],
        "dishes_with_corrupt_images": [],
        "dishes_with_incomplete_annotations": [],
        "annotation_file_found": False,
        "imagery_dir_found": False,
        "critical_issues": [],
        "warnings": [],
        "status": "UNKNOWN",
    }

    # Check annotation CSV
    nutrition_csv = raw_dir / "dish_nutrition_values.csv"
    if not nutrition_csv.exists():
        report["critical_issues"].append(f"dish_nutrition_values.csv not found at {nutrition_csv}")
        report["status"] = "FAIL"
        return report

    report["annotation_file_found"] = True

    # Load annotations
    try:
        df = pd.read_csv(nutrition_csv)
        logger.info(f"Loaded {len(df)} rows from dish_nutrition_values.csv")
    except Exception as e:
        report["critical_issues"].append(f"Failed to parse dish_nutrition_values.csv: {e}")
        report["status"] = "FAIL"
        return report

    # Check required columns
    missing_cols = [c for c in REQUIRED_MACRO_COLS + ["dish_id"] if c not in df.columns]
    if missing_cols:
        report["critical_issues"].append(f"Missing columns in CSV: {missing_cols}")
        report["status"] = "FAIL"
        return report

    # Get unique dish IDs
    dish_ids = df["dish_id"].dropna().unique().tolist()
    report["total_dishes"] = len(dish_ids)
    logger.info(f"Found {len(dish_ids)} unique dish IDs")

    # Check imagery directory
    if not imagery_dir.exists():
        report["imagery_dir_found"] = False
        report["warnings"].append(f"imagery/ directory not found at {imagery_dir}. Imagery checks skipped.")
        logger.warning("imagery/ directory not found — skipping imagery checks")
    else:
        report["imagery_dir_found"] = True
        # Check imagery for each dish
        for dish_id in dish_ids:
            ok, msg = check_imagery(dish_id, imagery_dir)
            if not ok:
                report["dishes_with_missing_imagery"].append({"dish_id": dish_id, "reason": msg})

    # Check annotation completeness
    for _, row in df.iterrows():
        dish_id = row.get("dish_id", "UNKNOWN")
        incomplete_fields = []
        for col in REQUIRED_MACRO_COLS:
            val = row.get(col)
            if pd.isna(val) or val < 0:
                incomplete_fields.append(col)
        if incomplete_fields:
            report["dishes_with_incomplete_annotations"].append({
                "dish_id": dish_id,
                "incomplete_fields": incomplete_fields,
            })

    # Determine status
    n_missing = len(report["dishes_with_missing_imagery"])
    n_incomplete = len(report["dishes_with_incomplete_annotations"])
    n_corrupt = len(report["dishes_with_corrupt_images"])

    if n_missing > 0:
        pct = n_missing / len(dish_ids) * 100
        if pct > 50:
            report["critical_issues"].append(f"{n_missing}/{len(dish_ids)} dishes missing imagery ({pct:.1f}%)")
        else:
            report["warnings"].append(f"{n_missing}/{len(dish_ids)} dishes missing imagery ({pct:.1f}%)")

    if n_incomplete > 0:
        report["critical_issues"].append(
            f"{n_incomplete} dishes have incomplete macro annotations (null or negative values)"
        )

    if report["critical_issues"]:
        report["status"] = "FAIL"
    elif report["warnings"]:
        report["status"] = "WARN"
    else:
        report["status"] = "PASS"

    # Write report
    report_path = reports_dir / "audit_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Audit report written to {report_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Audit Nutrition5k dataset integrity")
    parser.add_argument("--config", default="configs/data/data_config.yaml", help="Path to data config YAML")
    args = parser.parse_args()

    logger.info("=== NutriSnap Dataset Audit ===")
    report = audit_dataset(args.config)

    print(f"\n{'='*50}")
    print(f"Audit Status: {report['status']}")
    print(f"Total dishes: {report['total_dishes']}")
    print(f"Missing imagery: {len(report['dishes_with_missing_imagery'])}")
    print(f"Incomplete annotations: {len(report['dishes_with_incomplete_annotations'])}")

    if report["critical_issues"]:
        print("\nCRITICAL ISSUES:")
        for issue in report["critical_issues"]:
            print(f"  [X] {issue}")
        print(f"\nAudit FAILED. Fix critical issues before proceeding.")
        sys.exit(1)

    if report["warnings"]:
        print("\nWARNINGS:")
        for w in report["warnings"]:
            print(f"  [!] {w}")

    print(f"\nAudit {'PASSED' if report['status'] == 'PASS' else 'PASSED WITH WARNINGS'}.")
    sys.exit(0)


if __name__ == "__main__":
    main()
