"""Model Download Script.

Downloads pretrained models for development.
"""

import os
import sys
from pathlib import Path


def download_yolo_model(output_dir: str = "./ml/weights/") -> None:
    """Download pretrained YOLOv8-Nano model.
    
    Args:
        output_dir: Directory to save model.
    """
    print("Downloading YOLOv8-Nano pretrained model...")
    
    try:
        from ultralytics import YOLO
        
        # This downloads and caches the model
        model = YOLO("yolov8n.pt")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Export for reference
        output_path = Path(output_dir) / "yolov8n_pretrained.pt"
        print(f"✓ YOLOv8-Nano model available")
        print(f"  For custom training, fine-tune from pretrained weights")
        
    except ImportError:
        print("✗ ultralytics not installed. Run: pip install ultralytics")


def create_placeholder_portion_model(output_dir: str = "./ml/weights/") -> None:
    """Create a placeholder portion model.
    
    Args:
        output_dir: Directory to save model.
    """
    print("Creating placeholder portion model...")
    
    try:
        import joblib
        import numpy as np
        from sklearn.ensemble import RandomForestRegressor
        
        # Create a simple placeholder model
        X = np.random.rand(100, 7)
        y = 50 + X[:, 0] * 200 + np.random.rand(100) * 20
        
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        os.makedirs(output_dir, exist_ok=True)
        output_path = Path(output_dir) / "portion_model.joblib"
        joblib.dump(model, output_path)
        
        print(f"✓ Placeholder portion model saved to: {output_path}")
        print("  Note: Train on real data for production use")
        
    except ImportError:
        print("✗ Required packages not installed. Run: pip install joblib scikit-learn")


def download_depth_model() -> None:
    """Download Depth Anything V2 model info."""
    print("\nDepth Anything V2 model:")
    print("  This model is loaded from HuggingFace on first use")
    print("  Make sure you have: pip install transformers torch")
    print("  Model: depth-anything/Depth-Anything-V2-Small-hf")


def main() -> None:
    """Run all model downloads."""
    print("=" * 50)
    print("NutriSnap Model Downloader")
    print("=" * 50 + "\n")
    
    download_yolo_model()
    print()
    create_placeholder_portion_model()
    download_depth_model()
    
    print("\n" + "=" * 50)
    print("Model setup complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
