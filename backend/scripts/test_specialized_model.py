# test_specialized_model.py
from ultralytics import YOLO
import cv2
import os
import sys

# 1. Path to specialized weights
# The user should place the 'best.pt' file in the 'models/' directory
# and rename it to 'food_specialized_yolov8.pt' or update the path below.
weights_path = "models/food_specialized_yolov8.pt"

if not os.path.exists(weights_path):
    print(f"ERROR: Specialized weights not found at {weights_path}")
    print("Please download 'best.pt' from the SaladDetection-YOLOv8n project")
    print("and place it in the 'models/' directory.")
    sys.exit(1)

# 2. Load the model
print(f"Loading specialized model from {weights_path}...")
model = YOLO(weights_path)

# 3. Define folders
input_folder = "backend/datasets/uploads/"
output_folder = "backend/reports/specialized_test_results/"
os.makedirs(output_folder, exist_ok=True)

# 4. Run inference on images
print(f"Scanning images in {input_folder}...")
found_any = False
for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        image_path = os.path.join(input_folder, filename)
        print(f"Processing {filename}...")
        
        # Run detection with high resolution and low confidence
        results = model.predict(image_path, imgsz=1280, conf=0.1, save=True, project=output_folder, name="exp")
        
        if len(results[0].boxes) > 0:
            print(f"  -> SUCCESS: Detected {len(results[0].boxes)} items!")
            found_any = True
        else:
            print(f"  -> No detections.")

if found_any:
    print(f"\nDetection complete. Visual results saved to {output_folder}.")
else:
    print("\nNo detections found even with the specialized model.")
    print("Check diagnostic logs for image quality/compression details.")
