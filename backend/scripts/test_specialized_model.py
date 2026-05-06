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
    print(f"WARNING: Specialized weights not found at {weights_path}")
    print("Falling back to base yolov8n.pt for testing purposes...")
    weights_path = "yolov8n.pt"
    if not os.path.exists(weights_path):
        weights_path = "backend/yolov8n.pt" # Check in backend folder too
    
    if not os.path.exists(weights_path):
        print(f"ERROR: Base weights not found at {weights_path}")
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
        
        # Verify image exists and is readable
        test_img = cv2.imread(image_path)
        if test_img is None:
            print(f"  -> ERROR: Could not read image at {image_path}. Skipping.")
            continue
            
        print(f"Processing {filename} ({test_img.shape[1]}x{test_img.shape[0]})...")
        
        # Run detection with high resolution and low confidence
        try:
            results = model.predict(image_path, imgsz=1280, conf=0.1, save=True, project=output_folder, name="exp", verbose=False)
            
            if len(results[0].boxes) > 0:
                print(f"  -> SUCCESS: Detected {len(results[0].boxes)} items!")
                # Print labels of first 5 items
                labels = [results[0].names[int(c)] for c in results[0].boxes.cls[:5]]
                confs = [float(c) for c in results[0].boxes.conf[:5]]
                print(f"  -> Top items: {list(zip(labels, confs))}")
                found_any = True
            else:
                print(f"  -> No detections.")
        except Exception as e:
            print(f"  -> EXCEPTION during inference: {e}")

if found_any:
    print(f"\nDetection complete. Visual results saved to {output_folder}.")
else:
    print("\nNo detections found even with the specialized model.")
    print("Check diagnostic logs for image quality/compression details.")
