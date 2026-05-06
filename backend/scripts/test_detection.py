"""
test_detection.py — standalone OWL-ViT detection test.

Runs the real zero-shot detector on actual food images (CPU-safe, no GPU
or SAM2/GLPN required) and prints a clear detection report.

Usage (from backend/ directory):
    python scripts/test_detection.py
"""
import os
import sys
import time
from pathlib import Path

# ── Path setup ───────────────────────────────────────────────────────────────
BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

# ── Images to test ────────────────────────────────────────────────────────────
UPLOADS = BACKEND / "datasets" / "uploads"
TEST_IMAGES = [
    (UPLOADS / "test_biryani.jpg",    "Chicken Biryani"),
    (UPLOADS / "thali.jpg",           "Indian Thali"),
    (UPLOADS / "pizza_salad.jpg",     "Pizza + Salad"),
    (UPLOADS / "fruit_bowl.jpg",      "Fruit Bowl"),
]

# ── Query vocabulary ──────────────────────────────────────────────────────────
FOOD_QUERIES = [
    # Indian
    "biryani", "chicken biryani", "rice dish", "dal tadka", "paneer butter masala",
    "butter chicken", "chicken curry", "vegetable curry", "roti", "naan",
    "idli", "dosa", "samosa", "palak paneer", "thali", "chapati",
    # International
    "pizza", "burger", "sandwich", "pasta", "steak", "sushi",
    "salad", "soup", "fried rice", "noodles",
    "pancakes", "eggs", "grilled chicken", "fish fry", "french fries",
    # Generic catch-all
    "plate of food", "bowl of food", "meal", "food", "fruit", "vegetables",
    "bread", "dessert", "rice", "curry dish",
]

SEP = "─" * 60

def run_detection_tests():
    print(f"\n{'═'*60}")
    print("  NutriSnap — OWL-ViT Real Detection Test")
    print(f"{'═'*60}\n")

    # Load model once, reuse for all images
    print("Loading OWL-ViT (google/owlvit-base-patch32) on CPU...")
    load_start = time.perf_counter()
    try:
        from nutrisnap.pipeline.zero_shot import ZeroShotFoodDetector
        detector = ZeroShotFoodDetector(device="cpu", confidence_threshold=0.05)
        load_time = time.perf_counter() - load_start
        print(f"✅ Model loaded in {load_time:.1f}s\n")
    except Exception as e:
        print(f"❌ Failed to load OWL-ViT: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    results_summary = []
    all_passed = True

    for image_path, description in TEST_IMAGES:
        print(SEP)
        print(f"📷  Image    : {image_path.name}")
        print(f"🏷  Expected : {description}")

        if not image_path.exists():
            print(f"⚠️  SKIPPED — file not found")
            print()
            continue

        file_kb = image_path.stat().st_size / 1024
        print(f"📦  File size: {file_kb:.0f} KB")

        t0 = time.perf_counter()
        try:
            detections = detector.detect(str(image_path), FOOD_QUERIES, tiled=True)
            elapsed = time.perf_counter() - t0

            if detections:
                print(f"⏱  Inference: {elapsed:.2f}s")
                print(f"🎯  Detections ({len(detections)} items):")
                for d in sorted(detections, key=lambda x: x["confidence"], reverse=True):
                    box = d.get("bbox_xyxy", [0,0,0,0])
                    print(f"      [{d['confidence']:.3f}]  {d['label']:<30}  box={box}")
                results_summary.append((description, len(detections), "✅ PASS"))
            else:
                elapsed = time.perf_counter() - t0
                print(f"⏱  Inference: {elapsed:.2f}s")
                print(f"❌  ZERO DETECTIONS — no food found above threshold=0.05")
                results_summary.append((description, 0, "❌ FAIL"))
                all_passed = False

        except Exception as e:
            print(f"💥  Exception: {e}")
            import traceback; traceback.print_exc()
            results_summary.append((description, 0, "💥 ERROR"))
            all_passed = False

        print()

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"{'═'*60}")
    print("  Detection Summary")
    print(f"{'═'*60}")
    for desc, count, status in results_summary:
        print(f"  {status}  {desc:<28}  {count} detection(s)")

    print()
    if all_passed:
        print("✅  ALL IMAGES PRODUCED DETECTIONS — pipeline is working.")
    else:
        print("❌  Some images had zero detections. Check logs above.")
    print()

    detector.unload()


if __name__ == "__main__":
    run_detection_tests()
