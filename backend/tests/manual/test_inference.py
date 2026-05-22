import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.services.orchestrator import SequentialOrchestrator
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

def run_test():
    try:
        print("Initializing Orchestrator...")
        # Since we ran repair_gpu.py, torch should have CUDA available
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Detected device: {device}")
        
        orchestrator = SequentialOrchestrator(device=device)
        
        print("Creating dummy image...")
        with open("test_image.jpg", "wb") as f:
            f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xFF\xDB\x00C\x00\x02\x01\x01\x01\x01\x01\x02\x01\x01\x01\x02\x02\x02\x02\x02\x04\x03\x02\x02\x02\x02\x05\x04\x04\x03\x04\x06\x05\x06\x06\x06\x05\x06\x06\x06\x07\t\x08\x06\x07\t\x07\x06\x06\x08\x0B\x08\t\n\n\n\n\n\x06\x08\x0B\x0C\x0B\n\x0C\t\n\n\n\xFF\xC0\x00\x0B\x08\x00\x01\x00\x01\x01\x01\x11\x00\xFF\xC4\x00\x1F\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0B\xFF\xDA\x00\x08\x01\x01\x00\x00\x3F\x00\xD2\xCF\x20\xFF\xD9")
            
        print("Running prediction...")
        result = orchestrator.predict("test_image.jpg")
        print("Prediction result:")
        print(result.to_dict())
        
        print("Teardown...")
        orchestrator.teardown()
        
    except Exception as e:
        print(f"ERROR OCCURRED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
