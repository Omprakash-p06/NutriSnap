import ctypes
import os

torch_lib = (
    r"C:\Users\OM Prakash\Documents\NutriSnap\backend\venv\Lib\site-packages\torch\lib"
)
llama_dll = r"C:\Users\OM Prakash\Documents\NutriSnap\backend\venv\Lib\site-packages\llama_cpp\lib\llama.dll"


def test_load(path):
    try:
        ctypes.CDLL(path)
        print(f"SUCCESS: {os.path.basename(path)}")
        return True
    except Exception as e:
        print(f"FAILED: {os.path.basename(path)} - {e}")
        return False


print("Testing torch dependencies...")
os.add_dll_directory(torch_lib)

deps = [
    "cudart64_12.dll",
    "cublas64_12.dll",
    "cublasLt64_12.dll",
    "cufft64_11.dll",
    "curand64_10.dll",
    "cusolver64_11.dll",
    "cusparse64_12.dll",
]

for dep in deps:
    test_load(os.path.join(torch_lib, dep))

print("\nTesting llama.dll...")
test_load(llama_dll)
