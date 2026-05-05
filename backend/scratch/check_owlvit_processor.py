from transformers import OwlViTProcessor, OwlViTForObjectDetection
import torch
from PIL import Image
import requests

processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")
# model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32")

# Create a dummy image
image = Image.new("RGB", (640, 480), color="red")
queries = ["pizza", "apple"]

inputs = processor(text=[queries], images=image, return_tensors="pt")

# outputs = model(**inputs)
# Mock outputs
class MockOutput:
    def __init__(self):
        self.logits = torch.randn(1, 576, 2)
        self.pred_boxes = torch.rand(1, 576, 4)

outputs = MockOutput()

target_sizes = torch.Tensor([image.size[::-1]])

try:
    results = processor.post_process_grounded_object_detection(
        outputs, 
        threshold=0.1, 
        target_sizes=target_sizes,
        text_labels=[queries]
    )
    print("Success with post_process_grounded_object_detection")
    print(f"Results keys: {results[0].keys()}")
    print(f"Text labels in results: {results[0].get('text_labels')}")
except Exception as e:
    print(f"Failed with post_process_grounded_object_detection: {e}")

try:
    results = processor.image_processor.post_process_object_detection(
        outputs, 
        threshold=0.1, 
        target_sizes=target_sizes
    )
    print("Success with image_processor.post_process_object_detection")
    print(f"Results keys: {results[0].keys()}")
except Exception as e:
    print(f"Failed with image_processor.post_process_object_detection: {e}")
