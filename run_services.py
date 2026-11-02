"""
run_services.py
---------------
Orchestrates and runs all 5 microservices of the Customer Feedback Platform:
  - sentiment_service     (port 5002)
  - notification_service  (port 5004)
  - feedback_service      (port 5001)
  - analytics_service     (port 5003)
  - api_gateway           (port 5000)

Redirects stdout/stderr to logs/<service_name>.out / .err
Monitors health until all services are ready, and cleanly shuts them down on Ctrl+C.
"""

import os
import sys
import time
import signal
import subprocess
import urllib.request
import json

ROOT = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Select Python executable: prefer project's venv if available
VENV_PYTHON = os.path.join(ROOT, "venv", "Scripts", "python.exe")
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
PYTHON_EXEC = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable

SERVICES = [
    {
        "name": "sentiment_service",
        "script": os.path.join(ROOT, "src", "sentiment_service", "app.py"),
        "port": 5002,
        "health_url": "http://127.0.0.1:5002/health"
    },
    {
        "name": "notification_service",
        "script": os.path.join(ROOT, "src", "notification_service", "app.py"),
        "port": 5004,
        "health_url": "http://127.0.0.1:5004/health"
    },
    {
        "name": "feedback_service",
        "script": os.path.join(ROOT, "src", "feedback_service", "app.py"),
        "port": 5001,
        "health_url": "http://127.0.0.1:5001/health"
    },
    {
        "name": "analytics_service",
        "script": os.path.join(ROOT, "src", "analytics_service", "app.py"),
        "port": 5003,
        "health_url": "http://127.0.0.1:5003/health"
    },
    {
        "name": "api_gateway",
        "script": os.path.join(ROOT, "src", "api_gateway", "app.py"),
        "port": 5000,
        "health_url": "http://127.0.0.1:5000/health"
    },
]

processes = []
file_handles = []


def stop_all(signum=None, frame=None):
    print("\n[INFO] Stopping all microservices...")
    for p, name in processes:
        if p.poll() is None:
            print(f"  Terminating {name} (PID: {p.pid})...")
            p.terminate()
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
    for fh in file_handles:
        try:
            fh.close()
        except Exception:
            pass
    print("[INFO] All microservices stopped.")
    sys.exit(0)


def check_health(url, timeout=2):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False


def main():
    signal.signal(signal.SIGINT, stop_all)
    signal.signal(signal.SIGTERM, stop_all)

    print("=" * 60)
    print(" Starting AI Customer Feedback Platform Microservices")
    print(f" Using Python: {PYTHON_EXEC}")
    print("=" * 60)

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    for svc in SERVICES:
        out_path = os.path.join(LOGS_DIR, f"{svc['name']}.out")
        err_path = os.path.join(LOGS_DIR, f"{svc['name']}.err")

        out_file = open(out_path, "w", encoding="utf-8")
        err_file = open(err_path, "w", encoding="utf-8")
        file_handles.extend([out_file, err_file])

        cmd = [PYTHON_EXEC, svc["script"]]
        p = subprocess.Popen(
            cmd,
            stdout=out_file,
            stderr=err_file,
            cwd=ROOT,
            env=env
        )
        processes.append((p, svc["name"]))
        print(f"[*] Started {svc['name']} (PID: {p.pid}) on port {svc['port']}")

    print("\nWaiting for services to become healthy...")
    ready = {svc["name"]: False for svc in SERVICES}
    start_time = time.time()
    max_wait = 20  # seconds

    while time.time() - start_time < max_wait:
        all_ready = True
        for svc in SERVICES:
            name = svc["name"]
            if not ready[name]:
                if check_health(svc["health_url"]):
                    ready[name] = True
                    print(f"  [+] {name} is READY at {svc['health_url']}")
                else:
                    all_ready = False
        if all_ready:
            break
        time.sleep(1)

    if all(ready.values()):
        print("\n" + "=" * 60)
        print("  ALL SERVICES ARE RUNNING SUCCESSFULLY!")
        print("  Dashboard UI:   http://localhost:5000")
        print("  Gateway Health: http://localhost:5000/health")
        print("  API Docs:       docs/api_documentation.md")
        print("=" * 60)
        print("Press Ctrl+C to stop all services.\n")
    else:
        print("\n[WARNING] Some services may not have reported healthy within the timeout:")
        for name, is_ready in ready.items():
            print(f"  - {name}: {'READY' if is_ready else 'NOT READY (check logs)'}")

    # Keep running until interrupted
    try:
        while True:
            # Check if any process unexpectedly died
            for p, name in processes:
                code = p.poll()
                if code is not None:
                    print(f"[ERROR] Service {name} exited unexpectedly with code {code}.")
                    stop_all()
            time.sleep(2)
    except KeyboardInterrupt:
        stop_all()


if __name__ == "__main__":
    main()
