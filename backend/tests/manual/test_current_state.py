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


# We already copied 3 DLLs. Let's see if it works now.
print("Currently in llama_lib:")
for f in os.listdir(llama_lib):
    print(f" - {f}")

test_load_llama()
