import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Set working directory to backend
backend_dir = Path(r"c:\Users\OM Prakash\Documents\NutriSnap\backend")
sys.path.append(str(backend_dir))
os.environ["PYTHONPATH"] = str(backend_dir)
os.chdir(backend_dir)

from app.services.orchestrator import SequentialOrchestrator  # noqa: E402


def main():
    img_path = r"C:\Users\OM Prakash\Downloads\crispy-chicken-biryanigraphy-served-in-classic-indian-plate-style-photo_enhanced.jpg"
    print(f"Testing image: {img_path}")

    print("Initializing orchestrator...")
    orchestrator = SequentialOrchestrator(device="cuda", mock=False)

    print("Starting prediction...")
    try:
        t0 = time.time()
        result = orchestrator.predict(img_path)
        print(f"Prediction done in {time.time()-t0:.2f}s")
        res_dict = result.to_dict()
        print(f"Detected {len(res_dict['items'])} items:")
        for item in res_dict["items"]:
            print(
                f" - {item['label']} (conf: {item['confidence']:.2f}, vol: {item['volume_cm3']:.1f} cm3, kcal: {item['calories']:.1f})"
            )
        print(f"Total Calories: {res_dict['total_calories']:.1f} kcal")
        print(f"Validation: {res_dict['validation_summary']['reasoning']}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
