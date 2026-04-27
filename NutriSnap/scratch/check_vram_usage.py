import torch
from transformers import AutoProcessor, Sam2Model, pipeline, GLPNForDepthEstimation, GLPNImageProcessor
import time

def get_vram_usage():
    if not torch.cuda.is_available():
        return 0
    return torch.cuda.memory_allocated() / 1024**2

def main():
    print(f"Initial VRAM: {get_vram_usage():.2f} MB")
    
    # 1. Load SAM 2
    model_id = "facebook/sam2-hiera-tiny"
    processor = AutoProcessor.from_pretrained(model_id)
    model = Sam2Model.from_pretrained(model_id).to("cuda")
    pipe = pipeline(
        "mask-generation",
        model=model,
        image_processor=processor.image_processor,
        device=0,
    )
    print(f"VRAM after SAM 2: {get_vram_usage():.2f} MB")
    
    # 2. Load GLPN
    glpn_id = "vinvino02/glpn-nyu"
    glpn_processor = GLPNImageProcessor.from_pretrained(glpn_id)
    glpn_model = GLPNForDepthEstimation.from_pretrained(glpn_id).to("cuda")
    print(f"VRAM after GLPN: {get_vram_usage():.2f} MB")
    
    # 3. Simulate processing (just one image to check peak usage)
    from PIL import Image
    dummy_img = Image.new("RGB", (512, 512))
    
    print("Running SAM 2...")
    start = time.time()
    _ = pipe(dummy_img, points_per_batch=128, points_per_crop=16)
    print(f"SAM 2 took {time.time() - start:.2f}s")
    print(f"VRAM after SAM 2 run: {get_vram_usage():.2f} MB")
    
    print("Running GLPN...")
    start = time.time()
    inputs = glpn_processor(images=dummy_img, return_tensors="pt").to("cuda")
    with torch.no_grad():
        _ = glpn_model(**inputs)
    print(f"GLPN took {time.time() - start:.2f}s")
    print(f"VRAM after GLPN run: {get_vram_usage():.2f} MB")

if __name__ == "__main__":
    main()
