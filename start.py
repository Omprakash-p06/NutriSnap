import subprocess
import os
import sys
import platform
import threading
import signal

def get_backend_command():
    is_windows = platform.system() == "Windows"
    # Check for common venv names in the backend directory
    venv_options = ["venv", ".venv"]
    venv_dir = None
    for opt in venv_options:
        if os.path.exists(os.path.join("backend", opt)):
            venv_dir = opt
            break
    
    if not venv_dir:
        print(f"Error: Backend virtual environment not found in 'backend/' directory.", flush=True)
        print("Please run the setup script first to configure the environment: python setup.py", flush=True)
        sys.exit(1)

    if is_windows:
        python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        uvicorn_exe = os.path.join(venv_dir, "Scripts", "uvicorn.exe")
    else:
        python_exe = os.path.join(venv_dir, "bin", "python")
        uvicorn_exe = os.path.join(venv_dir, "bin", "uvicorn")

    if not os.path.exists(os.path.join("backend", python_exe)):
        print(f"Error: Python executable not found in backend/{venv_dir}", flush=True)
        print("Please run the setup script first: python setup.py", flush=True)
        sys.exit(1)

    # Use uvicorn directly from venv if available, otherwise use python -m uvicorn
    if os.path.exists(os.path.join("backend", uvicorn_exe)):
        return [uvicorn_exe, "app.main:app", "--host", "127.0.0.1", "--port", "5000", "--reload"]
    else:
        return [python_exe, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "5000", "--reload"]

def run_process(command, cwd, name):
    print(f"Starting {name}...", flush=True)
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            shell=(platform.system() == "Windows")
        )
        return process
    except Exception as e:
        print(f"Failed to start {name}: {e}", flush=True)
        return None

def find_gguf_model():
    """Return path to the first .gguf model file found, or None."""
    # Find model relative to current project root
    model_dir = os.path.join("backend", "models", "llm")
    if not os.path.exists(model_dir):
        return None
    for f in os.listdir(model_dir):
        if f.endswith(".gguf"):
            # Return absolute path so it works regardless of process cwd
            return os.path.abspath(os.path.join(model_dir, f))
    return None

def get_llama_server_command(model_path):
    """Build the llama.cpp server start command."""
    is_windows = platform.system() == "Windows"
    venv_options = ["venv", ".venv"]
    venv_dir = None
    for opt in venv_options:
        if os.path.exists(os.path.join("backend", opt)):
            venv_dir = opt
            break
    if not venv_dir:
        return None
    python_exe = os.path.join(
        venv_dir,
        "Scripts" if is_windows else "bin",
        "python.exe" if is_windows else "python"
    )
    return [python_exe, "-m", "nutrisnap.utils.local_llm_backend", "serve", "--model", model_path]

def main():
    is_windows = platform.system() == "Windows"
    
    # Check if frontend node_modules is present
    if not os.path.exists(os.path.join("frontend", "node_modules")):
        print("Error: Frontend 'node_modules' not found in 'frontend/' directory.", flush=True)
        print("Please run the setup script first to install dependencies: python setup.py", flush=True)
        sys.exit(1)
        
    backend_cmd = get_backend_command()
    frontend_cmd = ["npm.cmd" if is_windows else "npm", "run", "dev"]

    processes = []

    # Start llama.cpp server if a model is available (powers the chatbot)
    gguf_model = find_gguf_model()
    if gguf_model:
        llama_cmd = get_llama_server_command(gguf_model)
        if llama_cmd:
            llama_proc = run_process(llama_cmd, "backend", "llama.cpp Server")
            if llama_proc:
                processes.append(llama_proc)
                print(f"  Model: {gguf_model}", flush=True)
    else:
        print("llama.cpp: No GGUF model found in backend/models/llm/. Chatbot will use cloud fallback.", flush=True)
        print("  Run: python backend/scripts/setup_local_llm.py --no-download", flush=True)

    backend_proc = run_process(backend_cmd, "backend", "Backend")
    frontend_proc = run_process(frontend_cmd, "frontend", "Frontend")
    processes += [backend_proc, frontend_proc]

    def signal_handler(sig, frame):
        print("\nShutting down...")
        for p in processes:
            if p:
                p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    
    print("\nNutriSnap is running! Press Ctrl+C to stop both servers.")
    
    # Wait for processes to finish
    for p in processes:
        if p:
            p.wait()

if __name__ == "__main__":
    main()
