import argparse
import json
import os
import sys
from datetime import datetime

from loguru import logger

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.orchestrator import SequentialOrchestrator


def batch_verify(upload_dir, mock=False, min_size=10240):
    logger.info(
        f"Batch verifying pipeline with images in: {upload_dir} (mock={mock}, min_size={min_size})"
    )

    if not os.path.exists(upload_dir):
        logger.error(f"Upload directory not found: {upload_dir}")
        return

    images = [
        f for f in os.listdir(upload_dir) if f.endswith((".jpg", ".png", ".jpeg"))
    ]
    valid_images = []
    for img in images:
        path = os.path.join(upload_dir, img)
        if os.path.getsize(path) >= min_size:
            valid_images.append(path)
        else:
            logger.debug(f"Skipping small file: {img} ({os.path.getsize(path)} bytes)")

    logger.info(f"Found {len(valid_images)} valid images to test.")

    results = []
    device = "cpu"
    orchestrator = SequentialOrchestrator(device=device, mock=mock)

    for img_path in valid_images:
        logger.info(f"Testing {os.path.basename(img_path)}...")
        try:
            start_time = datetime.now()
            result = orchestrator.predict(img_path)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            summary = {
                "image": os.path.basename(img_path),
                "status": "success",
                "duration_sec": duration,
                "items_detected": len(result.items),
                "total_calories": result.total_calories,
                "items": [
                    {
                        "label": item["label"],
                        "confidence": item.get("confidence", 0),
                        "source": item.get("source", "unknown"),
                        "calories": item["calories"],
                        "mass_g": item["mass_g"],
                        "health_score": item.get("health_score", "N/A"),
                    }
                    for item in result.items
                ],
                "validation_summary": result.validation_summary,
            }
            results.append(summary)
            logger.info(f"  Success: {len(result.items)} items found.")
        except Exception as e:
            logger.error(f"  Failed {os.path.basename(img_path)}: {e}")
            results.append(
                {
                    "image": os.path.basename(img_path),
                    "status": "failed",
                    "error": str(e),
                }
            )

    # Save results to a report file
    report_path = os.path.join(
        os.path.dirname(__file__), "..", "reports", "batch_verification_report.json"
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Batch verification complete. Report saved to: {report_path}")

    # Print summary
    success_count = sum(1 for r in results if r["status"] == "success")
    total_items = sum(
        r.get("items_detected", 0) for r in results if r["status"] == "success"
    )
    logger.info(
        f"Summary: {success_count}/{len(valid_images)} images processed successfully."
    )
    logger.info(f"Total items detected: {total_items}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="Use mock orchestrator")
    parser.add_argument(
        "--min-size", type=int, default=10240, help="Minimum file size in bytes"
    )
    args = parser.parse_args()

    upload_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "datasets", "uploads")
    )
    batch_verify(upload_dir, mock=args.mock, min_size=args.min_size)
