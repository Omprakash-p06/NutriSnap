"""Setup script for llama.cpp local inference in NutriSnap.

Detects hardware, installs the correct llama-cpp-python build (CUDA / Vulkan /
OpenVINO / CPU), and optionally downloads a Gemma 4 GGUF model.

Usage::

    # Full setup (detect hardware, install, download model)
    python scripts/setup_local_llm.py

    # Only detect hardware (no install)
    python scripts/setup_local_llm.py --detect-only

    # Skip model download (you already have a GGUF file)
    python scripts/setup_local_llm.py --no-download

    # Use a specific model variant
    python scripts/setup_local_llm.py --model-variant gemma-4-4b-q4_k_m

    # Force a specific backend (skip auto-detection)
    python scripts/setup_local_llm.py --backend cuda

After setup, start the server:
    python -m nutrisnap.utils.local_llm_backend serve --model models/llm/gemma-4-2b-q4_k_m.gguf

Then set in .env:
    LLM_PROVIDER=local
    LOCAL_LLM_MODEL=gemma-4-2b-q4_k_m   (filename without .gguf)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# ─── Model catalogue ──────────────────────────────────────────────────────────
# Hugging Face GGUF repos for Gemma 4 (Google's official GGUF releases)
_MODELS = {
    "gemma-4-2b-q4_k_m": {
        "repo": "google/gemma-4-2b-GGUF",
        "filename": "gemma-4-2b-q4_k_m.gguf",
        "size_gb": 1.8,
        "min_vram_gb": 2.5,
        "description": "Gemma 4 2B, 4-bit quantized (recommended for RTX 3050)",
    },
    "gemma-4-4b-q4_k_m": {
        "repo": "google/gemma-4-4b-GGUF",
        "filename": "gemma-4-4b-q4_k_m.gguf",
        "size_gb": 3.5,
        "min_vram_gb": 4.5,
        "description": "Gemma 4 4B, 4-bit quantized (better JSON, needs 6GB+ VRAM for full GPU)",
    },
    "gemma-4-2b-q8": {
        "repo": "google/gemma-4-2b-GGUF",
        "filename": "gemma-4-2b-q8_0.gguf",
        "size_gb": 3.2,
        "min_vram_gb": 4.0,
        "description": "Gemma 4 2B, 8-bit quantized (higher quality, more VRAM)",
    },
}

_DEFAULT_MODEL = "gemma-4-2b-q4_k_m"
_MODEL_DIR = Path("models/llm")

# ─── llama-cpp-python wheel indices by backend ────────────────────────────────
# Pre-built wheels from abetlen's index (avoids C++ compilation)
_WHEEL_INDICES = {
    "cuda": {
        "cu124": "https://abetlen.github.io/llama-cpp-python/whl/cu124",
        "cu121": "https://abetlen.github.io/llama-cpp-python/whl/cu121",
        "cu118": "https://abetlen.github.io/llama-cpp-python/whl/cu118",
    },
    "vulkan": None,   # Must compile from source with CMAKE_ARGS
    "openvino": None, # Must compile from source with CMAKE_ARGS
    "cpu": "https://abetlen.github.io/llama-cpp-python/whl/cpu",
}

# CMake build args for source compilation
_CMAKE_ARGS = {
    "vulkan": "-DGGML_VULKAN=on",
    "openvino": "-DGGML_OPENVINO=on",
    "cpu": "",
}


def _run(cmd: list[str], env: dict | None = None) -> int:
    """Run a subprocess, streaming output. Returns exit code."""
    full_env = {**os.environ, **(env or {})}
    proc = subprocess.Popen(cmd, env=full_env, text=True)
    proc.wait()
    return proc.returncode


def _detect() -> dict:
    """Run hardware detection and return info dict."""
    # Import here so setup script works even before nutrisnap is fully installed
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from nutrisnap.utils.local_llm_backend import detect_hardware  # noqa: PLC0415
        hw = detect_hardware()
        return hw.to_dict()
    except ImportError:
        # Fallback: minimal detection
        hw: dict = {"backend": "cpu", "gpu_name": None, "vram_gb": None, "n_gpu_layers": 0}
        try:
            import torch  # noqa: PLC0415
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                hw["backend"] = "cuda"
                hw["gpu_name"] = props.name
                hw["vram_gb"] = props.total_memory / 1e9
        except ImportError:
            pass
        return hw


def _install_llama_cpp(backend: str, cuda_version: str = "cu124") -> bool:
    """Install llama-cpp-python with the correct backend.

    Returns True on success.
    """
    print(f"\n[setup] Installing llama-cpp-python for backend: {backend}")

    if backend == "cuda":
        wheel_index = _WHEEL_INDICES["cuda"].get(cuda_version, _WHEEL_INDICES["cuda"]["cu124"])
        cmd = [
            sys.executable, "-m", "pip", "install",
            "llama-cpp-python",
            "--extra-index-url", wheel_index,
            "--upgrade",
        ]
        print(f"  Using pre-built CUDA wheel from: {wheel_index}")

    elif backend == "cpu":
        wheel_index = _WHEEL_INDICES["cpu"]
        cmd = [
            sys.executable, "-m", "pip", "install",
            "llama-cpp-python",
            "--extra-index-url", wheel_index,
            "--upgrade",
        ]
        print("  Using pre-built CPU wheel")

    else:
        # Vulkan or OpenVINO: must compile from source
        cmake_arg = _CMAKE_ARGS.get(backend, "")
        env_override = {"CMAKE_ARGS": cmake_arg} if cmake_arg else {}
        print(f"  Compiling from source with CMAKE_ARGS={cmake_arg!r}")
        print("  This may take 5–15 minutes depending on your CPU...")
        cmd = [sys.executable, "-m", "pip", "install", "llama-cpp-python", "--upgrade", "--no-binary=llama-cpp-python"]
        rc = _run(cmd, env=env_override)
        if rc != 0:
            print(f"[ERROR] Compilation failed (exit {rc}). Check CMake and build tools.")
            return False
        return True

    rc = _run(cmd)
    if rc != 0:
        print(f"[ERROR] pip install failed (exit {rc})")
        return False
    return True


def _verify_install() -> bool:
    """Verify llama-cpp-python is importable."""
    try:
        import llama_cpp  # noqa: F401, PLC0415
        print(f"[OK] llama-cpp-python is installed")
        return True
    except ImportError as e:
        print(f"[ERROR] llama-cpp-python import failed: {e}")
        return False


def _download_model(model_key: str) -> Optional[Path]:
    """Download a GGUF model from Hugging Face Hub.

    Returns the path to the downloaded file, or None on failure.
    """
    info = _MODELS.get(model_key)
    if not info:
        print(f"[ERROR] Unknown model key: {model_key}. Options: {list(_MODELS)}")
        return None

    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    dest = _MODEL_DIR / info["filename"]

    if dest.exists():
        print(f"[OK] Model already downloaded: {dest}")
        return dest

    print(f"\n[setup] Downloading {model_key} (~{info['size_gb']:.1f} GB)...")
    print(f"  Repo: {info['repo']}")
    print(f"  File: {info['filename']}")

    # Try huggingface_hub first (most reliable)
    try:
        from huggingface_hub import hf_hub_download  # noqa: PLC0415
        path = hf_hub_download(
            repo_id=info["repo"],
            filename=info["filename"],
            local_dir=str(_MODEL_DIR),
            repo_type="model",
        )
        print(f"[OK] Downloaded to: {path}")
        return Path(path)
    except ImportError:
        print("  huggingface_hub not installed. Installing...")
        _run([sys.executable, "-m", "pip", "install", "huggingface_hub", "-q"])
        try:
            from huggingface_hub import hf_hub_download  # noqa: PLC0415
            path = hf_hub_download(
                repo_id=info["repo"],
                filename=info["filename"],
                local_dir=str(_MODEL_DIR),
                repo_type="model",
            )
            print(f"[OK] Downloaded to: {path}")
            return Path(path)
        except Exception as e:
            print(f"[ERROR] Download failed: {e}")
            return None
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        print(f"  Manual download URL: https://huggingface.co/{info['repo']}/resolve/main/{info['filename']}")
        print(f"  Save to: {dest}")
        return None


def _print_next_steps(hw: dict, model_path: Path | None, backend: str) -> None:
    """Print concise next-steps instructions."""
    print("\n" + "=" * 60)
    print("SETUP COMPLETE — Next Steps")
    print("=" * 60)

    model_str = str(model_path) if model_path else "models/llm/<your-model>.gguf"

    print(f"\n1. Start the llama.cpp server:")
    print(f"   python -m nutrisnap.utils.local_llm_backend serve --model {model_str}")
    print()
    print("2. Or start it in your shell startup script (runs in background):")
    print(f"   python -m llama_cpp.server --model {model_str} \\")
    print(f"       --host 127.0.0.1 --port 8000 --n_gpu_layers {hw.get('n_gpu_layers', 0)}")
    print()
    print("3. Set in backend/.env:")
    print("   LLM_PROVIDER=local")
    if model_path:
        model_name = model_path.stem
        print(f"   LOCAL_LLM_MODEL={model_name}")
    print("   LOCAL_LLM_URL=http://127.0.0.1:8000/v1")
    print()
    print(f"Detected backend : {backend}")
    if hw.get('gpu_name'):
        print(f"GPU              : {hw['gpu_name']} ({hw.get('vram_gb', '?'):.1f} GB VRAM)")
        print(f"GPU layers       : {hw.get('n_gpu_layers', 0)} (offloaded to GPU)")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Setup llama.cpp local inference for NutriSnap",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--detect-only", action="store_true", help="Only detect hardware, skip install")
    parser.add_argument("--no-download", action="store_true", help="Skip model download")
    parser.add_argument(
        "--model-variant",
        choices=list(_MODELS.keys()),
        default=_DEFAULT_MODEL,
        help=f"GGUF model variant to download (default: {_DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--backend",
        choices=["cuda", "vulkan", "openvino", "cpu"],
        default=None,
        help="Force a specific backend (skip auto-detection)",
    )
    parser.add_argument(
        "--cuda-version",
        choices=["cu124", "cu121", "cu118"],
        default="cu124",
        help="CUDA toolkit version for pre-built wheel (default: cu124)",
    )
    args = parser.parse_args()

    print("\n=== NutriSnap — llama.cpp Local Inference Setup ===\n")

    # 1. Detect hardware
    print("[1/4] Detecting hardware...")
    hw = _detect()
    backend = args.backend or hw.get("backend", "cpu")

    print(f"  Backend    : {backend}")
    if hw.get("gpu_name"):
        print(f"  GPU        : {hw['gpu_name']}")
        print(f"  VRAM       : {hw.get('vram_gb', 0):.1f} GB")
        print(f"  GPU layers : {hw.get('n_gpu_layers', 0)}")
    else:
        print("  GPU        : none (CPU-only mode)")

    if args.detect_only:
        import json  # noqa: PLC0415
        print(json.dumps(hw, indent=2))
        return

    # 2. Install llama-cpp-python
    print("\n[2/4] Installing llama-cpp-python...")
    ok = _install_llama_cpp(backend, cuda_version=args.cuda_version)
    if not ok:
        print("[WARN] Install may have failed. Continuing to verify...")

    # 3. Verify
    print("\n[3/4] Verifying installation...")
    if not _verify_install():
        print("\n[FATAL] llama-cpp-python could not be imported. See error above.")
        print("  Try: pip install llama-cpp-python --upgrade")
        sys.exit(1)

    # 4. Download model
    model_path = None
    if not args.no_download:
        print(f"\n[4/4] Downloading model: {args.model_variant}...")
        model_path = _download_model(args.model_variant)
    else:
        print("\n[4/4] Skipping model download (--no-download)")
        # Check if a model already exists
        existing = list(_MODEL_DIR.glob("*.gguf"))
        if existing:
            model_path = existing[0]
            print(f"  Found existing model: {model_path}")

    _print_next_steps(hw, model_path, backend)


if __name__ == "__main__":
    main()
