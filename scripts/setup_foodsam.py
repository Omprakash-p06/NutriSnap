"""Download and verify FoodSAM model weights.

Downloads:
  - SAM ViT-H checkpoint (~2.4 GB) -> third_party/FoodSAM/checkpoints/sam_vit_h_4b8939.pth

Usage:
    python scripts/setup_foodsam.py [--checkpoint-dir PATH]
"""
import argparse
import hashlib
import sys
import time
from pathlib import Path

import requests

# SAM ViT-H weights (Meta official)
SAM_WEIGHTS = {
    "url": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth",
    "filename": "sam_vit_h_4b8939.pth",
    "sha256_prefix": "a7bf3b02f3",  # first 10 hex chars for quick verify
    "size_mb": 2564,
}

DEFAULT_CHECKPOINT_DIR = Path("third_party/FoodSAM/checkpoints")


def verify_file(path: Path, sha_prefix: str) -> bool:
    """Quick SHA256 prefix check."""
    if not path.exists():
        return False
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().startswith(sha_prefix)


def download_with_retry(url: str, dest: Path, max_retries: int = 5) -> bool:
    """Download file with streaming and basic retry logic."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    # Check for existing partial download (simple resume logic not implemented for simplicity,
    # we just restart but with better stream handling)
    
    for attempt in range(max_retries):
        try:
            print(f"[v] Download attempt {attempt + 1}/{max_retries}...")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(dest, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            done = int(50 * downloaded / total_size)
                            percent = (100 * downloaded / total_size)
                            sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {percent:3.1f}%")
                            sys.stdout.flush()
            
            print("\n[OK] Download complete.")
            return True
            
        except (requests.exceptions.RequestException, IOError) as e:
            print(f"\n[!] Error during download: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"[!] Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print("[X] Max retries exceeded.")
                return False
    return False


def main():
    parser = argparse.ArgumentParser(description="Download FoodSAM model weights")
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=DEFAULT_CHECKPOINT_DIR,
        help="Directory to store model checkpoints",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("FoodSAM Weight Setup (Robust Downloader)")
    print("=" * 60)

    checkpoint_dir = args.checkpoint_dir
    dest = checkpoint_dir / SAM_WEIGHTS["filename"]

    if dest.exists():
        print(f"[OK] SAM weights file found: {dest}")
        if verify_file(dest, SAM_WEIGHTS["sha256_prefix"]):
            print(f"[OK] SHA256 prefix verified. Setup ready.")
            sys.exit(0)
        else:
            print(f"[!] SHA256 mismatch - file may be corrupt. Re-downloading.")

    success = download_with_retry(SAM_WEIGHTS["url"], dest)
    
    if success:
        print("[#] Verifying SHA256...")
        if verify_file(dest, SAM_WEIGHTS["sha256_prefix"]):
            print("[OK] SHA256 prefix verified.")
        else:
            print("[X] SHA256 verification failed after download!")
            sys.exit(1)
    else:
        print("[X] Setup failed.")
        sys.exit(1)

    print()
    print("=" * 60)
    print("[OK] FoodSAM setup complete!")
    print(f"    Checkpoint: {dest}")
    print("=" * 60)


if __name__ == "__main__":
    main()
