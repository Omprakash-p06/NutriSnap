#!/usr/bin/env python3
"""
NutriSnap Model Setup Script
==============================
Run this once after cloning to download all required AI model weights.

Usage:
    cd NutriSnap/backend
    python scripts/download_models.py

All models are downloaded to the Hugging Face cache (~/.cache/huggingface/)
and the Ultralytics cache (~/.cache/ultralytics/).
No model files need to be committed to Git.
"""

import sys
import time
from pathlib import Path


def print_header(text: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_step(step: str, model: str, size: str) -> None:
    print(f"\n[{step}] Downloading {model} (~{size})...")


def download_huggingface_models() -> None:
    """Pre-fetch all Hugging Face models to local cache."""
    try:
        from transformers import (
            AutoProcessor,
            GLPNForDepthEstimation,
            GLPNImageProcessor,
            OwlViTForObjectDetection,
            OwlViTProcessor,
            Sam2Model,
        )
    except ImportError:
        print("ERROR: transformers not installed. Run: pip install -r requirements.txt")
        sys.exit(1)

    models = [
        {
            "name": "OWL-ViT (Zero-Shot Food Detector)",
            "id": "google/owlvit-base-patch32",
            "size": "615 MB",
            "loader": lambda mid: (
                OwlViTProcessor.from_pretrained(mid),
                OwlViTForObjectDetection.from_pretrained(mid),
            ),
        },
        {
            "name": "SAM 2 (Food Segmentation)",
            "id": "facebook/sam2-hiera-tiny",
            "size": "156 MB",
            "loader": lambda mid: (
                AutoProcessor.from_pretrained(mid),
                Sam2Model.from_pretrained(mid),
            ),
        },
        {
            "name": "GLPN (Depth Estimation)",
            "id": "vinvino02/glpn-nyu",
            "size": "245 MB",
            "loader": lambda mid: (
                GLPNImageProcessor.from_pretrained(mid),
                GLPNForDepthEstimation.from_pretrained(mid),
            ),
        },
    ]

    for i, m in enumerate(models, 1):
        print_step(f"{i}/{len(models)}", m["name"], m["size"])
        t0 = time.time()
        try:
            m["loader"](m["id"])
            elapsed = time.time() - t0
            print(f"    ✓ Done in {elapsed:.1f}s")
        except Exception as e:
            print(f"    ✗ Failed: {e}")
            print(
                f"    You can retry with: python -c \"from transformers import AutoProcessor; AutoProcessor.from_pretrained('{m['id']}')\""
            )


def download_yolo() -> None:
    """Download YOLOv8n from Ultralytics."""
    print_step("4/4", "YOLOv8n (Food Detection)", "6 MB")
    try:
        from ultralytics import YOLO

        t0 = time.time()
        YOLO("yolov8n.pt")  # triggers auto-download to Ultralytics cache
        elapsed = time.time() - t0
        print(f"    ✓ Done in {elapsed:.1f}s")
    except ImportError:
        print("    ✗ ultralytics not installed. Run: pip install -r requirements.txt")
    except Exception as e:
        print(f"    ✗ Failed: {e}")


def verify_custom_weights() -> None:
    """Check that custom-trained model files are present."""
    print("\n[Checking] Custom-trained model weights...")
    models_dir = Path(__file__).parent.parent / "models"
    required = ["efficientnet_mass_regressor_calibrator.joblib"]

    all_ok = True
    for fname in required:
        fpath = models_dir / fname
        if fpath.exists():
            print(f"    ✓ {fname} ({fpath.stat().st_size} bytes)")
        else:
            print(f"    ✗ MISSING: {fname}")
            print(f"      Expected at: {fpath}")
            all_ok = False

    if not all_ok:
        print("\n  WARNING: Some custom weights are missing.")
        print(
            "  These are committed to the repository — ensure you ran `git clone` correctly."
        )


def main() -> None:
    print_header("NutriSnap — AI Model Download Script")
    print("""
  This script downloads all required AI model weights.
  Total download size: ~1.05 GB (cached locally, not in repo)

  Make sure you have a stable internet connection.
  Models download to:
    - HF Hub:       ~/.cache/huggingface/hub/
    - Ultralytics:  ~/AppData/Local/Ultralytics/ (Windows)
                    ~/.cache/ultralytics/       (Linux/macOS)
""")

    input("  Press ENTER to start, or Ctrl+C to cancel...")

    print_header("Downloading Models")
    download_huggingface_models()
    download_yolo()
    verify_custom_weights()

    print_header("Setup Complete!")
    print("""
  All models are ready. You can now start NutriSnap:

    # From project root:
    python start.py

    # Or manually:
    cd backend && uvicorn app.main:app --reload --port 5000
    cd frontend && npm run dev

  Set SKIP_AI_INIT=false in backend/.env to enable real AI inference.
""")


if __name__ == "__main__":
    main()
