import ctypes
import os
import shutil

torch_lib = (
    r"C:\Users\OM Prakash\Documents\NutriSnap\backend\venv\Lib\site-packages\torch\lib"
)
llama_lib = r"C:\Users\OM Prakash\Documents\NutriSnap\backend\venv\Lib\site-packages\llama_cpp\lib"
llama_dll = os.path.join(llama_lib, "llama.dll")


def test_load_llama():
    try:
        ctypes.CDLL(llama_dll)
        print("SUCCESS: llama.dll loaded")
        return True
    except Exception as e:
        print(f"FAILED: llama.dll - {e}")
        return False


# Clear DLL directory to be sure
print("Testing without any extra paths...")
test_load_llama()

print("\nAdding ONLY cudart64_12.dll path...")
# We can't really "add" just one file to search path, only directories.
# So I'll copy cudart64_12.dll to llama_lib and see if it works.

shutil.copy(os.path.join(torch_lib, "cudart64_12.dll"), llama_lib)
test_load_llama()

print("\nAdding cublas64_12.dll...")
shutil.copy(os.path.join(torch_lib, "cublas64_12.dll"), llama_lib)
test_load_llama()

print("\nAdding cublasLt64_12.dll...")
shutil.copy(os.path.join(torch_lib, "cublasLt64_12.dll"), llama_lib)
test_load_llama()
