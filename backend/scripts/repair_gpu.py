import subprocess
import sys
import os

def run_command(command):
    print(f"Running: {command}")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        text=True
    )
    for line in process.stdout:
        print(line, end="")
    process.wait()
    return process.returncode

def main():
    print("=== NutriSnap GPU Repair Tool ===")
    
    # 1. Uninstall current CPU versions
    print("\nPhase 1: Removing CPU-only PyTorch...")
    run_command(f'"{sys.executable}" -m pip uninstall -y torch torchvision torchaudio')
    
    # 2. Install CUDA versions (using cu124 for RTX 30/40 series)
    print("\nPhase 2: Installing CUDA-enabled PyTorch (cu124)...")
    # Using cu124 is best for RTX 3050 and modern drivers
    install_cmd = f'"{sys.executable}" -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124'
    result = run_command(install_cmd)
    
    if result != 0:
        print("\nERROR: Installation failed. Attempting fallback to cu121...")
        install_cmd_fallback = f'"{sys.executable}" -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121'
        run_command(install_cmd_fallback)

    # 3. Verification
    print("\nPhase 3: Verifying GPU Access...")
    verify_script = "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
    run_command(f'"{sys.executable}" -c "{verify_script}"')
    
    print("\nDone. Please restart NutriSnap using 'python start.py'.")

if __name__ == "__main__":
    main()
