import os
import sys
import argparse
from loguru import logger

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.orchestrator import SequentialOrchestrator

def verify_pipeline(image_path, mock=False):
    logger.info(f"Verifying pipeline with image: {image_path} (mock={mock})")
    
    if not os.path.exists(image_path):
        logger.error(f"Image not found: {image_path}")
        return False

    try:
        device = "cpu" # Default to CPU for verification if CUDA not available
        orchestrator = SequentialOrchestrator(device=device, mock=mock)
        result = orchestrator.predict(image_path)
        
        logger.info("Pipeline run successful!")
        logger.info(f"Items detected: {len(result.items)}")
        for item in result.items:
            logger.info(f"  - {item['label']}: {item['calories']} kcal, {item['mass_g']}g")
        
        logger.info(f"Total Calories: {result.total_calories}")
        logger.info(f"Validation Summary: {result.validation_summary}")
        
        return True
    except Exception as e:
        logger.error(f"Pipeline verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, help="Path to test image")
    parser.add_argument("--mock", action="store_true", help="Use mock orchestrator")
    args = parser.parse_args()
    
    # Use a default image if none provided
    test_image = args.image
    if not test_image:
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "datasets", "uploads")
        if os.path.exists(upload_dir):
            images = [f for f in os.listdir(upload_dir) if f.endswith(".jpg")]
            if images:
                test_image = os.path.join(upload_dir, images[0])
    
    if not test_image:
        logger.error("No test image provided and none found in uploads.")
        sys.exit(1)
        
    success = verify_pipeline(test_image, mock=args.mock)
    sys.exit(0 if success else 1)
