import sys
import os

def check_system():
    print("--- Python & OS Details ---")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    print("\n--- PyTorch & GPU Details ---")
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        cuda_avail = torch.cuda.is_available()
        print(f"CUDA Available (GPU support): {cuda_avail}")
        if cuda_avail:
            print(f"CUDA Device Count: {torch.cuda.device_count()}")
            print(f"GPU Name: {torch.cuda.get_device_name(0)}")
            print(f"Current CUDA Device ID: {torch.cuda.current_device()}")
        else:
            print("CUDA is NOT available. PyTorch will run on CPU.")
    except ImportError:
        print("PyTorch is not installed in the current Python environment.")
    except Exception as e:
        print(f"Error checking PyTorch: {e}")

    print("\n--- Transformers Details ---")
    try:
        import transformers
        print(f"Transformers version: {transformers.__version__}")
    except ImportError:
        print("Transformers is not installed in the current Python environment.")
    except Exception as e:
        print(f"Error checking Transformers: {e}")

    print("\n--- Memory (RAM) Details ---")
    try:
        # Check RAM on Windows
        if sys.platform == "win32":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            total_ram_gb = stat.ullTotalPhys / (1024**3)
            avail_ram_gb = stat.ullAvailPhys / (1024**3)
            print(f"Total Physical RAM: {total_ram_gb:.2f} GB")
            print(f"Available Physical RAM: {avail_ram_gb:.2f} GB")
            print(f"Memory Load: {stat.dwMemoryLoad}%")
        else:
            # Unix-like fallback
            import psutil
            mem = psutil.virtual_memory()
            print(f"Total RAM: {mem.total / (1024**3):.2f} GB")
            print(f"Available RAM: {mem.available / (1024**3):.2f} GB")
    except Exception as e:
        print(f"Could not retrieve memory details: {e}")

if __name__ == "__main__":
    check_system()
