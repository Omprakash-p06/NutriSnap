import torch
import numpy as np
from PIL import Image
import sys
import os
import cv2

# Ensure we can import from nutrisnap
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from nutrisnap.pipeline.segmenter import FoodSegmenterSAM2
from nutrisnap.pipeline.depth import DepthEstimatorGLPN
from nutrisnap.models.efficientnet_regressor import EfficientNetRegressor
import joblib
import albumentations as A
from albumentations.pytorch import ToTensorV2

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Path to input RGB image")
    parser.add_argument("--checkpoint", default="checkpoints/efficientnet_mass_regressor.pth")
    parser.add_argument("--calibrator", default="checkpoints/efficientnet_mass_regressor_calibrator.joblib")
    args = parser.parse_args()

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # 1. Load SAM2 and GLPN
    print("Loading SAM2 and GLPN...")
    segmenter = FoodSegmenterSAM2(device=str(device))
    depth_estimator = DepthEstimatorGLPN(device=str(device))

    # 2. Load model and calibrator
    print("Loading regression model...")
    model = EfficientNetRegressor().to(device)
    model.load_state_dict(torch.load(args.checkpoint, map_location=device))
    model.eval()
    calibrator = joblib.load(args.calibrator)

    # 3. Load image and get mask / depth map
    print("Running segmentation and depth estimation...")
    seg_result = segmenter.segment(args.image)
    depth_array = depth_estimator.estimate(args.image)
    
    # Extract combined mask
    mask_array = seg_result["combined_mask"] # shape (H, W), values 0 or 255
    
    # Also load the original RGB image to build the tensor
    image = np.array(Image.open(args.image).convert('RGB'))
    
    print("Preprocessing for the model...")
    # Resize RGB to 224x224
    transform_rgb = A.Compose([
        A.Resize(224, 224),
        # Assuming model needs standard imagenet normalization
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ])
    
    # Resize mask and depth to 224x224
    transform_gray = A.Compose([
        A.Resize(224, 224),
        ToTensorV2(),
    ])

    rgb_tensor = transform_rgb(image=image)['image'].unsqueeze(0).to(device) # (1, 3, 224, 224)
    
    # Convert mask to [0, 1] range float32
    mask_norm = (mask_array > 0).astype(np.float32)
    mask_tensor = transform_gray(image=mask_norm)['image'].unsqueeze(0).to(device) # (1, 1, 224, 224)
    
    # Normalize depth (simple min-max or just keep it as is if model trained without norm)
    depth_norm = depth_array.astype(np.float32)
    depth_tensor = transform_gray(image=depth_norm)['image'].unsqueeze(0).to(device) # (1, 1, 224, 224)

    # 5. Build 5-channel composite: RGB (3) + mask (1) + depth (1)
    composite = torch.cat([rgb_tensor, mask_tensor, depth_tensor], dim=1) # (1, 5, 224, 224)

    # 6. Extract volume scalar from depth map
    mask_bool = (mask_tensor > 0.5)
    if mask_bool.sum() > 0:
        volume = depth_tensor[mask_bool].mean().unsqueeze(0).unsqueeze(0).cpu() # (1, 1)
    else:
        volume = torch.tensor([[0.0]]) # (1, 1)

    print(f"Estimated volume feature: {volume.item():.4f}")

    # 7. Predict mass
    print("Predicting mass...")
    with torch.no_grad():
        pred_log = model(composite, volume.to(device))
        pred_grams_raw = torch.expm1(pred_log).cpu().numpy()[0,0]

    # 8. Apply calibration
    pred_grams_calibrated = calibrator.predict([[pred_grams_raw]])[0]

    print(f"\n--- RESULTS ---")
    print(f"Predicted mass (raw): {pred_grams_raw:.1f} g")
    print(f"Predicted mass (calibrated): {pred_grams_calibrated:.1f} g")

if __name__ == '__main__':
    main()
