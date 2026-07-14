import os
import sys
import subprocess

def kill_process_on_port(port):
    print(f"Checking port {port}...")
    try:
        # Use netstat on Windows to find the PID listening on the port
        output = subprocess.check_output(f'netstat -aon | findstr :{port}', shell=True).decode('utf-8', errors='ignore')
        pids = set()
        for line in output.splitlines():
            parts = line.strip().split()
            if len(parts) >= 5 and 'LISTENING' in parts:
                pid = parts[-1]
                pids.add(int(pid))
        
        if not pids:
            print(f"No active listening process found on port {port}.")
            return
            
        for pid in pids:
            print(f"Found process {pid} on port {port}. Terminating...")
            # Use taskkill to force kill the process
            subprocess.run(f"taskkill /F /PID {pid}", shell=True)
            print(f"Successfully killed process {pid}.")
    except subprocess.CalledProcessError:
        print(f"No process listening on port {port} (or netstat call failed).")
    except Exception as e:
        print(f"Error while killing process on port {port}: {e}")

if __name__ == "__main__":
    # We will check ports 8000 (FastAPI), 5173 (Vite), and 5174 (Vite)
    ports = [8000, 5173, 5174]
    for port in ports:
        kill_process_on_port(port)
    print("\nPort cleanup completed.")
