import os
import subprocess
import sys
import time
import signal
import io
from pymongo import MongoClient

# Force UTF-8 output to avoid UnicodeEncodeErrors in various terminals
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# --- Configuration ---
TELEMETRY_SCRIPT = "real_time_engine_telemetry.py"
DASHBOARD_SCRIPT = "app.py"
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

# Detect Virtual Environment
if os.path.exists(".venv"):
    if os.name == 'nt':
        PYTHON_EXE = os.path.join(".venv", "Scripts", "python.exe")
    else:
        PYTHON_EXE = os.path.join(".venv", "bin", "python")
else:
    PYTHON_EXE = sys.executable

def check_mongodb():
    print(f"[*] Checking MongoDB connection: {MONGODB_URI}")
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
        client.server_info()
        print("[+] MongoDB is ONLINE.")
        return True
    except Exception as e:
        print(f"[-] MongoDB is OFFLINE: {e}")
        return False

def main():
    if not check_mongodb():
        print("ERROR: Please start MongoDB before running the system.")
        return

    processes = []

    def cleanup(sig, frame):
        print("\n\n[*] Shutting down system...")
        for p in processes:
            print(f"[*] Terminating {p.args}...")
            p.terminate()
        print("[+] System offline. Goodbye.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)

    print("\n" + "="*50)
    print("   AEROSPACE PREDICTIVE ANALYTICS - UNIFIED LAUNCHER")
    print("="*50 + "\n")

    # 1. Start Telemetry Simulation
    print(f"[*] Starting Telemetry Simulation ({TELEMETRY_SCRIPT})...")
    telemetry_proc = subprocess.Popen([PYTHON_EXE, TELEMETRY_SCRIPT])
    processes.append(telemetry_proc)

    # 2. Start NEXUS Command Center (Flask)
    print(f"[*] Starting NEXUS Command Center ({DASHBOARD_SCRIPT})...")
    dashboard_proc = subprocess.Popen([PYTHON_EXE, DASHBOARD_SCRIPT])
    processes.append(dashboard_proc)

    print("\n[+] SYSTEM IS RUNNING.")
    print("[!] Press Ctrl+C to stop both processes.\n")
    print("-" * 50)
    
    try:
        while True:
            # Check if processes are still alive
            if telemetry_proc.poll() is not None:
                print("[-] Telemetry process died unexpectedly.")
                break
            if dashboard_proc.poll() is not None:
                print("[-] Dashboard process died unexpectedly.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == "__main__":
    main()
