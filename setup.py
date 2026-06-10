#!/usr/bin/env python3
"""
NutriSnap Project Setup Script
==============================
Run this once after cloning the repository.
It automates:
1. Creating .env files from .env.example
2. Downloading frontend dependencies (npm install)
3. Creating backend virtual environment (venv)
4. Installing backend python dependencies (pip install)
5. Downloading required AI models (optional, ~1.05 GB)
"""

import os
import platform
import shutil
import subprocess
import sys


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def run_command(command, cwd=None, shell=False):
    """Executes a command and returns True if successful, False otherwise."""
    try:
        # We don't capture stdout/stderr so the user sees real-time progress and interactive prompts
        result = subprocess.run(command, cwd=cwd, shell=shell, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(
            f"\n[Error] Command failed with exit code {e.returncode}: {' '.join(command) if isinstance(command, list) else command}"
        )
        return False
    except Exception as e:
        print(f"\n[Error] Failed to execute command: {e}")
        return False


def setup_env_files():
    print_header("1. Setting up Environment Variables")

    backend_env_example = os.path.join("backend", ".env.example")
    backend_env = os.path.join("backend", ".env")
    frontend_env_example = os.path.join("frontend", ".env.example")
    frontend_env = os.path.join("frontend", ".env")

    # Setup backend .env
    if os.path.exists(backend_env_example):
        if not os.path.exists(backend_env):
            print(f"Creating {backend_env} from example...")
            shutil.copy(backend_env_example, backend_env)
            print(
                "  ✓ Created. Please configure your API keys (e.g. GEMINI_API_KEY) in backend/.env if needed."
            )
        else:
            print("  ✓ backend/.env already exists.")
    else:
        print("  ✗ Warning: backend/.env.example not found.")

    # Setup frontend .env
    if os.path.exists(frontend_env_example):
        if not os.path.exists(frontend_env):
            print(f"Creating {frontend_env} from example...")
            shutil.copy(frontend_env_example, frontend_env)
            print("  ✓ Created.")
        else:
            print("  ✓ frontend/.env already exists.")
    else:
        print("  ✗ Warning: frontend/.env.example not found.")


def install_frontend_deps():
    print_header("2. Installing Frontend Dependencies")

    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"

    # Check if npm is installed
    if not shutil.which(npm_cmd) and not shutil.which("npm"):
        print("✗ Error: Node.js/npm is not installed or not found in PATH.")
        print("Please install Node.js (https://nodejs.org) and try again.")
        return False

    print("Running 'npm install' in frontend/ directory...")
    success = run_command(
        [npm_cmd if shutil.which(npm_cmd) else "npm", "install"], cwd="frontend"
    )
    if success:
        print("  ✓ Frontend dependencies installed successfully.")
    return success


def setup_backend_venv():
    print_header("3. Setting up Backend Virtual Environment")

    is_windows = platform.system() == "Windows"
    venv_dir = os.path.join("backend", "venv")

    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment in {venv_dir}...")
        success = run_command([sys.executable, "-m", "venv", venv_dir])
        if not success:
            print("✗ Failed to create virtual environment.")
            return False
        print("  ✓ Virtual environment created.")
    else:
        print("  ✓ Virtual environment already exists.")

    # Determine executables inside virtual environment
    if is_windows:
        python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        python_exe = os.path.join(venv_dir, "bin", "python")
        pip_exe = os.path.join(venv_dir, "bin", "pip")

    if not os.path.exists(python_exe):
        print(f"✗ Error: Python executable not found in {python_exe}")
        return False

    print("\nUpgrading pip inside virtual environment...")
    run_command([python_exe, "-m", "pip", "install", "--upgrade", "pip"])

    # Install dependencies
    requirements_txt = os.path.join("backend", "requirements.txt")
    requirements_dev_txt = os.path.join("backend", "requirements-dev.txt")

    if os.path.exists(requirements_txt):
        print(f"\nInstalling backend dependencies from {requirements_txt}...")
        args = [pip_exe, "install", "-r", requirements_txt]

        # Optimize PyTorch with CUDA index URL for Windows/Linux
        if is_windows or platform.system() == "Linux":
            args += ["--extra-index-url", "https://download.pytorch.org/whl/cu121"]

        success = run_command(args)
        if not success:
            print("✗ Failed to install backend dependencies.")
            return False

    if os.path.exists(requirements_dev_txt):
        print(f"\nInstalling dev dependencies from {requirements_dev_txt}...")
        success = run_command([pip_exe, "install", "-r", requirements_dev_txt])
        if not success:
            print("✗ Warning: Failed to install dev dependencies.")

    print("  ✓ Backend Python dependencies installed successfully.")
    return True


def download_ai_models():
    print_header("4. Download AI Model Weights (Optional)")

    venv_dir = os.path.join("backend", "venv")
    is_windows = platform.system() == "Windows"
    python_exe = os.path.join(
        venv_dir,
        "Scripts" if is_windows else "bin",
        "python.exe" if is_windows else "python",
    )
    download_script = os.path.join("backend", "scripts", "download_models.py")

    if not os.path.exists(download_script):
        print(
            "✗ Model download script not found at backend/scripts/download_models.py."
        )
        return

    user_choice = (
        input("Do you want to download the AI model weights (~1GB) now? (y/n) [y]: ")
        .strip()
        .lower()
    )
    if user_choice in ("", "y", "yes"):
        print("\nLaunching download_models.py script...")
        # Run it using the virtual environment python so it has transformers and ultralytics installed
        run_command([python_exe, download_script])
    else:
        print("\nSkipping model download. You can download them later using:")
        if is_windows:
            print(f"  {python_exe} {download_script}")
        else:
            print(f"  {python_exe} {download_script}")


def main():
    print_header("NutriSnap Development Environment Setup")
    print("This script will prepare NutriSnap for first-time use.")

    setup_env_files()
    frontend_ok = install_frontend_deps()
    backend_ok = setup_backend_venv()

    if frontend_ok and backend_ok:
        download_ai_models()
        print_header("Setup Complete!")
        print("""
You are ready to run the project.

Start the servers concurrently by running:
  python start.py

Or run manually:
  # Backend
  cd backend
  venv\\Scripts\\activate (Windows) or source venv/bin/activate (Unix)
  uvicorn app.main:app --reload --port 5000
  
  # Frontend
  cd frontend
  npm run dev
""")
    else:
        print_header("Setup Failed")
        print("Please resolve the issues listed above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
