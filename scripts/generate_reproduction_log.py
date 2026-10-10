import os
import subprocess
import json
import time
from datetime import datetime, timezone

targets = {
    "data": ["python", "scripts/data_processing/build_event_catalogue.py"],
    "baseline": ["python", "scripts/evaluate_baselines.py"],
    "enkf": ["python", "scripts/experiment_enkf.py"],
    "gnn_lstm": ["python", "scripts/experiment_gnn_lstm.py"],
    "uncertainty": ["python", "scripts/experiment_uncertainty.py"],
    "cascade": ["python", "scripts/experiment_cascade.py"],
    "compound": ["python", "scripts/experiment_compound_risk.py"],
    "warnings": ["python", "scripts/experiment_human_factors.py"],
    "faults": ["python", "scripts/experiment_fault_tolerance.py"],
    "transfer": ["python", "scripts/experiment_city_transfer.py"],
    "test": ["pytest", "backend/tests/"]
}

results = {
    "status": "INCOMPLETE",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "tests_passed": False,
    "metrics_generated": False,
    "random_seed": 42,
    "targets": {}
}

all_passed = True
os.environ["PYTHONPATH"] = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
# using the active venv executable
python_exe = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\backend\venv\Scripts\python.exe"
pytest_exe = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\backend\venv\Scripts\pytest.exe"

for name, cmd in targets.items():
    print(f"Running {name}...")
    start_time = time.time()
    
    # replace 'python' or 'pytest' with absolute path
    if cmd[0] == "python":
        cmd[0] = python_exe
    elif cmd[0] == "pytest":
        cmd[0] = pytest_exe
        
    cwd = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    duration = time.time() - start_time
    
    success = (result.returncode == 0)
    if not success:
        all_passed = False
        print(f"Failed {name}!\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        
    results["targets"][name] = {
        "success": success,
        "return_code": result.returncode,
        "duration_seconds": round(duration, 2),
        "stdout_tail": result.stdout[-500:] if result.stdout else "",
        "stderr_tail": result.stderr[-500:] if result.stderr else ""
    }

results["tests_passed"] = results["targets"]["test"]["success"]
results["metrics_generated"] = all_passed
results["status"] = "PREPRINT READY" if all_passed else "NOT READY"

try:
    git_hash = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=r"C:\Users\gokul\Desktop\PROJECTS\climatetwin").stdout.strip()
    results["git_commit"] = git_hash
except Exception:
    results["git_commit"] = "unknown"

with open(r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\results\reproduction_log.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"Reproduction run completed. All passed: {all_passed}")
