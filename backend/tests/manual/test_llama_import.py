import ctypes
import os
import sys

torch_lib = (
    r"C:\Users\OM Prakash\Documents\NutriSnap\backend\venv\Lib\site-packages\torch\lib"
)
if os.path.exists(torch_lib):
    print(f"Adding {torch_lib} to DLL search path")
    os.add_dll_directory(torch_lib)

try:
    import llama_cpp

    print("Successfully imported llama_cpp!")
except Exception as e:
    print(f"Failed to import llama_cpp: {e}")
