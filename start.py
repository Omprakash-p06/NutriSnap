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
        print(f"Error: Backend virtual environment not found in 'backend/' directory. Tried: {', '.join(venv_options)}", flush=True)
        print("Please create it first using: python -m venv backend/venv", flush=True)
        sys.exit(1)

    if is_windows:
        python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        uvicorn_exe = os.path.join(venv_dir, "Scripts", "uvicorn.exe")
    else:
        python_exe = os.path.join(venv_dir, "bin", "python")
        uvicorn_exe = os.path.join(venv_dir, "bin", "uvicorn")

    if not os.path.exists(os.path.join("backend", python_exe)):
        print(f"Error: Python executable not found in backend/{venv_dir}", flush=True)
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

def main():
    is_windows = platform.system() == "Windows"
    backend_cmd = get_backend_command()
    frontend_cmd = ["npm.cmd" if is_windows else "npm", "run", "dev"]

    backend_proc = run_process(backend_cmd, "backend", "Backend")
    frontend_proc = run_process(frontend_cmd, "frontend", "Frontend")

    processes = [backend_proc, frontend_proc]

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
