"""llama.cpp hardware detection and server process management for NutriSnap.

Detects the best available compute backend in priority order:
    CUDA (NVIDIA GPU) > Vulkan (any GPU) > OpenVINO (Intel CPU/iGPU) > CPU

Then manages a llama_cpp.server subprocess with optimal launch flags for that backend.

Usage (programmatic)::

    from nutrisnap.utils.local_llm_backend import LlamaCppBackend

    backend = LlamaCppBackend()
    info = backend.detect()
    print(info)   # {'backend': 'cuda', 'gpu_name': 'NVIDIA GeForce RTX 3050', ...}

    # Start the server (blocks until healthy or timeout)
    backend.start_server(model_path="models/gemma-4-2b-q4.gguf")

Usage (CLI)::

    python -m nutrisnap.utils.local_llm_backend detect
    python -m nutrisnap.utils.local_llm_backend serve --model models/gemma-4-2b-q4.gguf

Environment variables (all optional, auto-detected if absent)::

    LLAMA_BACKEND        Override backend: cuda | vulkan | openvino | cpu
    LLAMA_MODEL_PATH     Path to GGUF model file
    LLAMA_N_GPU_LAYERS   Number of transformer layers to offload to GPU (-1 = all)
    LLAMA_N_THREADS      Number of CPU threads (default: physical core count)
    LLAMA_CTX_SIZE       Context window size (default: 2048, enough for validation)
    LLAMA_PORT           Port for llama_cpp.server (default: 8008)
    LLAMA_HOST           Host for llama_cpp.server (default: 127.0.0.1)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

# ─── GPU layer recommendations for Gemma models on common VRAM configs ────────
# Key: VRAM in GB (approximate), Value: n_gpu_layers to offload
# Gemma 4 2B Q4_K_M has ~1.8GB weights; full offload at 4GB+
# Gemma 4 4B Q4_K_M has ~3.5GB weights; full offload at 6GB+
_GPU_LAYERS_BY_VRAM = {
    2.0: 10,   # Partial offload — main memory bottleneck
    3.0: 20,
    4.0: 26,   # RTX 3050 (4GB): full Gemma 2B Q4 offload
    6.0: 35,   # Full Gemma 4B Q4 offload
    8.0: 35,
    12.0: 35,
    24.0: 35,
}


def _recommend_gpu_layers(vram_gb: float) -> int:
    """Return recommended n_gpu_layers for available VRAM."""
    for threshold, layers in sorted(_GPU_LAYERS_BY_VRAM.items(), reverse=True):
        if vram_gb >= threshold:
            return layers
    return 0  # CPU only


class HardwareInfo:
    """Result of hardware detection."""

    def __init__(
        self,
        backend: str,
        gpu_name: Optional[str] = None,
        vram_gb: Optional[float] = None,
        cpu_cores: int = 4,
        cpu_features: list[str] | None = None,
        n_gpu_layers: int = 0,
    ) -> None:
        self.backend = backend          # "cuda" | "vulkan" | "openvino" | "cpu"
        self.gpu_name = gpu_name
        self.vram_gb = vram_gb
        self.cpu_cores = cpu_cores
        self.cpu_features = cpu_features or []
        self.n_gpu_layers = n_gpu_layers

    def __repr__(self) -> str:
        gpu = f"{self.gpu_name} ({self.vram_gb:.1f}GB VRAM)" if self.gpu_name else "none"
        return (
            f"HardwareInfo(backend={self.backend!r}, gpu={gpu!r}, "
            f"cpu_cores={self.cpu_cores}, n_gpu_layers={self.n_gpu_layers})"
        )

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "gpu_name": self.gpu_name,
            "vram_gb": self.vram_gb,
            "cpu_cores": self.cpu_cores,
            "cpu_features": self.cpu_features,
            "n_gpu_layers": self.n_gpu_layers,
        }


def _detect_cuda() -> Optional[HardwareInfo]:
    """Detect NVIDIA CUDA availability via torch."""
    try:
        import torch  # noqa: PLC0415
        if not torch.cuda.is_available():
            return None
        props = torch.cuda.get_device_properties(0)
        vram_gb = props.total_memory / 1e9
        layers = _recommend_gpu_layers(vram_gb)
        logger.info(f"CUDA detected: {props.name} ({vram_gb:.1f} GB), recommending {layers} GPU layers")
        return HardwareInfo(
            backend="cuda",
            gpu_name=props.name,
            vram_gb=vram_gb,
            n_gpu_layers=layers,
            cpu_cores=os.cpu_count() or 4,
        )
    except ImportError:
        # torch not installed — try nvidia-smi as fallback
        return _detect_cuda_via_smi()


def _detect_cuda_via_smi() -> Optional[HardwareInfo]:
    """Fallback CUDA detection via nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return None
        line = result.stdout.strip().splitlines()[0]
        name, vram_mib = line.split(",")
        vram_gb = float(vram_mib.strip()) / 1024.0
        layers = _recommend_gpu_layers(vram_gb)
        logger.info(f"CUDA detected via nvidia-smi: {name.strip()} ({vram_gb:.1f} GB)")
        return HardwareInfo(backend="cuda", gpu_name=name.strip(), vram_gb=vram_gb, n_gpu_layers=layers)
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        return None


def _detect_vulkan() -> Optional[HardwareInfo]:
    """Detect Vulkan GPU via vulkaninfo CLI."""
    if shutil.which("vulkaninfo") is None:
        # vulkaninfo not on PATH — try the Vulkan SDK default location on Windows
        win_path = Path("C:/VulkanSDK")
        candidates = list(win_path.glob("*/Bin/vulkaninfo.exe")) if win_path.exists() else []
        if not candidates:
            return None
        vulkaninfo_bin = str(candidates[-1])
    else:
        vulkaninfo_bin = "vulkaninfo"

    try:
        result = subprocess.run(
            [vulkaninfo_bin, "--summary"],
            capture_output=True, text=True, timeout=8,
        )
        if result.returncode != 0 or "GPU" not in result.stdout:
            return None
        # Extract GPU name from vulkaninfo output
        for line in result.stdout.splitlines():
            if "deviceName" in line:
                gpu_name = line.split("=")[-1].strip()
                logger.info(f"Vulkan detected: {gpu_name}")
                # Vulkan offload layer count: conservative (no VRAM info available)
                return HardwareInfo(
                    backend="vulkan",
                    gpu_name=gpu_name,
                    n_gpu_layers=20,  # conservative default for Vulkan
                    cpu_cores=os.cpu_count() or 4,
                )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _detect_openvino() -> Optional[HardwareInfo]:
    """Detect Intel OpenVINO availability."""
    try:
        import openvino as ov  # noqa: PLC0415
        core = ov.Core()
        devices = core.available_devices
        has_gpu = any("GPU" in d for d in devices)
        has_npu = any("NPU" in d for d in devices)
        device_str = ", ".join(devices)
        logger.info(f"OpenVINO detected. Devices: {device_str}")
        # OpenVINO runs on CPU/iGPU — no traditional GPU layer offload
        return HardwareInfo(
            backend="openvino",
            gpu_name=f"Intel ({device_str})" if has_gpu or has_npu else None,
            n_gpu_layers=0,  # OpenVINO handles its own compute graph
            cpu_cores=os.cpu_count() or 4,
            cpu_features=["openvino"],
        )
    except ImportError:
        return None
    except Exception as exc:
        logger.debug(f"OpenVINO check failed: {exc}")
        return None


def _detect_cpu_features() -> list[str]:
    """Return detected CPU instruction set extensions."""
    features = []
    try:
        import cpuinfo  # py-cpuinfo  # noqa: PLC0415
        info = cpuinfo.get_cpu_info()
        flags = info.get("flags", [])
        for f in ("avx512f", "avx2", "avx", "fma"):
            if f in flags:
                features.append(f)
    except ImportError:
        # Fallback: try reading /proc/cpuinfo on Linux
        try:
            cpuinfo_text = Path("/proc/cpuinfo").read_text()
            for f in ("avx512", "avx2", "avx", "fma"):
                if f in cpuinfo_text:
                    features.append(f)
        except (FileNotFoundError, PermissionError):
            pass
    return features


def detect_hardware(override_backend: Optional[str] = None) -> HardwareInfo:
    """Detect the best available compute backend for llama.cpp.

    Priority: CUDA > Vulkan > OpenVINO > CPU

    Args:
        override_backend: Force a specific backend ("cuda"|"vulkan"|"openvino"|"cpu").

    Returns:
        HardwareInfo describing the best available backend.
    """
    env_override = override_backend or os.getenv("LLAMA_BACKEND", "").lower()

    if env_override:
        logger.info(f"Backend override: {env_override!r}")
        # Still run detection for metadata (VRAM, GPU name)
        cuda_info = _detect_cuda()
        if env_override == "cuda":
            return cuda_info or HardwareInfo(backend="cpu", cpu_cores=os.cpu_count() or 4)
        if env_override in ("vulkan", "openvino"):
            hw = _detect_vulkan() if env_override == "vulkan" else _detect_openvino()
            return hw or HardwareInfo(backend="cpu", cpu_cores=os.cpu_count() or 4)
        return HardwareInfo(backend="cpu", cpu_cores=os.cpu_count() or 4, cpu_features=_detect_cpu_features())

    # Auto-detect: highest performance backend wins
    cuda = _detect_cuda()
    if cuda:
        return cuda

    vulkan = _detect_vulkan()
    if vulkan:
        return vulkan

    openvino = _detect_openvino()
    if openvino:
        return openvino

    # Pure CPU
    features = _detect_cpu_features()
    logger.info(f"No GPU detected. CPU-only mode. Features: {features or ['generic']}")
    return HardwareInfo(
        backend="cpu",
        cpu_cores=os.cpu_count() or 4,
        cpu_features=features,
    )


def build_server_args(hw: HardwareInfo, model_path: str) -> list[str]:
    """Build llama_cpp.server launch arguments for the detected hardware.

    Returns a list suitable for subprocess.Popen.
    """
    port = int(os.getenv("LLAMA_PORT", "8008"))
    host = os.getenv("LLAMA_HOST", "127.0.0.1")
    ctx_size = int(os.getenv("LLAMA_CTX_SIZE", "2048"))

    # Thread count: use physical cores (not hyperthreads) for best llama.cpp perf
    n_threads = int(os.getenv("LLAMA_N_THREADS", str(max(1, (os.cpu_count() or 4) // 2))))

    # GPU layer override from env
    n_gpu_layers = int(os.getenv("LLAMA_N_GPU_LAYERS", str(hw.n_gpu_layers)))

    args = [
        sys.executable, "-m", "llama_cpp.server",
        "--model", model_path,
        "--host", host,
        "--port", str(port),
        "--n_ctx", str(ctx_size),
        "--n_threads", str(n_threads),
        "--n_gpu_layers", str(n_gpu_layers),
    ]

    # Backend-specific flags
    if hw.backend == "cuda":
        # llama.cpp auto-uses CUDA if compiled with GGML_CUDA; no extra flags needed
        logger.info(
            f"llama.cpp server: CUDA backend, "
            f"offloading {n_gpu_layers} layers to {hw.gpu_name}"
        )
    elif hw.backend == "vulkan":
        # GGML_VULKAN compile flag needed — runtime flag selects device 0
        logger.info(f"llama.cpp server: Vulkan backend, {n_gpu_layers} GPU layers")
    elif hw.backend == "openvino":
        # OpenVINO backend: disable GPU offload, let OV handle compute graph
        logger.info("llama.cpp server: OpenVINO backend (CPU/iGPU via Intel)")
    else:
        # Pure CPU: set batch size low to keep latency manageable
        args += ["--n_batch", "128"]
        logger.info(f"llama.cpp server: CPU-only, {n_threads} threads, features: {hw.cpu_features}")

    return args


class LlamaCppBackend:
    """Lifecycle manager for the llama_cpp.server subprocess.

    Starts, health-checks, and gracefully shuts down a llama.cpp server
    process with hardware-optimal flags.

    Example::

        backend = LlamaCppBackend()
        hw = backend.detect()
        backend.start_server("models/gemma-4-2b-q4_k_m.gguf")
        # ... use the OpenAI-compatible API at http://127.0.0.1:8000/v1
        backend.stop_server()
    """

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None
        self._hw: Optional[HardwareInfo] = None

    def detect(self) -> HardwareInfo:
        """Run hardware detection and cache the result."""
        self._hw = detect_hardware()
        return self._hw

    @property
    def port(self) -> int:
        return int(os.getenv("LLAMA_PORT", "8008"))

    @property
    def base_url(self) -> str:
        host = os.getenv("LLAMA_HOST", "127.0.0.1")
        return f"http://{host}:{self.port}/v1"

    def is_server_running(self) -> bool:
        """Check if the llama.cpp server is accepting connections."""
        try:
            import urllib.request  # noqa: PLC0415
            url = f"http://{os.getenv('LLAMA_HOST', '127.0.0.1')}:{self.port}/health"
            with urllib.request.urlopen(url, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def start_server(
        self,
        model_path: str,
        wait_timeout: int = 60,
    ) -> bool:
        """Start the llama_cpp.server subprocess.

        Args:
            model_path: Path to the GGUF model file.
            wait_timeout: Seconds to wait for the server to become healthy.

        Returns:
            True if server started successfully, False otherwise.
        """
        if self.is_server_running():
            logger.info(f"llama.cpp server already running at {self.base_url}")
            return True

        if self._hw is None:
            self._hw = detect_hardware()

        model = Path(model_path)
        if not model.exists():
            logger.error(
                f"Model file not found: {model_path}. "
                "Run: python scripts/setup_local_llm.py --download"
            )
            return False

        args = build_server_args(self._hw, str(model.resolve()))
        logger.info(f"Starting llama.cpp server: {' '.join(args)}")

        try:
            # We don't capture stdout/stderr here so that logs from llama_cpp.server
            # flow through to the main terminal, making them visible to the user.
            self._process = subprocess.Popen(
                args,
                stdout=None,
                stderr=None,
            )
        except FileNotFoundError:
            logger.error(
                "llama-cpp-python not installed. "
                "Run: python scripts/setup_local_llm.py"
            )
            return False

        # Wait for health endpoint to respond
        deadline = time.time() + wait_timeout
        while time.time() < deadline:
            if self._process.poll() is not None:
                logger.error("llama.cpp server process exited unexpectedly")
                return False
            if self.is_server_running():
                logger.info(f"llama.cpp server ready at {self.base_url}")
                return True
            time.sleep(1.5)

        logger.error(f"llama.cpp server did not become healthy within {wait_timeout}s")
        return False

    def stop_server(self) -> None:
        """Gracefully terminate the server subprocess."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            logger.info("llama.cpp server stopped")
        self._process = None


# Module-level singleton
_backend: Optional[LlamaCppBackend] = None


def get_backend() -> LlamaCppBackend:
    global _backend  # noqa: PLW0603
    if _backend is None:
        _backend = LlamaCppBackend()
    return _backend


# ─── CLI entry point ──────────────────────────────────────────────────────────

def _cli() -> None:
    import argparse  # noqa: PLC0415
    import json  # noqa: PLC0415

    parser = argparse.ArgumentParser(
        description="llama.cpp hardware detection and server management"
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("detect", help="Detect best compute backend and print info")

    serve_p = sub.add_parser("serve", help="Start llama.cpp server with optimal flags")
    serve_p.add_argument("--model", required=True, help="Path to GGUF model file")
    serve_p.add_argument("--timeout", type=int, default=60)

    args = parser.parse_args()

    if args.cmd == "detect":
        hw = detect_hardware()
        print(json.dumps(hw.to_dict(), indent=2))

    elif args.cmd == "serve":
        backend = LlamaCppBackend()
        backend.detect()
        ok = backend.start_server(args.model, wait_timeout=args.timeout)
        sys.exit(0 if ok else 1)

    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
