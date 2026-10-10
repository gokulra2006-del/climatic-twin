import subprocess
import time
import urllib.request
import urllib.error
import json
import numpy as np
import os
import sys
from datetime import datetime, timezone

def run_phase7_validation():
    print("=== Phase 7 End-to-End Latency Validation ===")
    
    # 1. Start FastAPI backend
    print("Starting FastAPI backend...")
    proc = subprocess.Popen(
        [r"backend\venv\Scripts\python.exe", "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\backend"
    )
    
    # Wait for startup
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for _ in range(15):
        try:
            req = urllib.request.Request("http://127.0.0.1:8000/health")
            with opener.open(req, timeout=2) as res:
                if res.status == 200:
                    break
        except Exception:
            time.sleep(1)
            
    base_url = "http://127.0.0.1:8000"
    num_events = 15
    e2e_latencies = []
    ingestion_latencies = []
    inference_latencies = []
    api_latencies = []
    
    failed = False
    
    try:
        # A. Ping health
        print("Pinging health endpoint...")
        req = urllib.request.Request(f"{base_url}/health")
        with opener.open(req) as res:
            assert res.status == 200
            
        print(f"Executing {num_events} simulated telemetry test runs...")
        
        for i in range(num_events):
            # Simulate sensor telemetry creation
            source_time = time.time()
            
            # Simulated sensor payload (simulating typical monsoon rainfall event)
            payload = {
                "source_timestamp": source_time,
                "rainfall_daily": float(40.0 + np.random.normal(0, 5)),
                "rainfall_3d_sum": 95.0,
                "rainfall_5d_sum": 120.0,
                "rainfall_7d_sum": 145.0,
                "temp_mean": 26.5,
                "temp_max": 31.0,
                "temp_min": 24.0,
                "dew_point_mean": 23.5,
                "wind_speed_mean": 3.5,
                "POONDI": 2800.0,
                "CHOLAVARAM": 900.0,
                "REDHILLS": 2900.0,
                "CHEMBARAMBAKKAM": 3100.0
            }
            
            # Simulate brief transmission lag over Cellular (50-100ms)
            time.sleep(np.random.uniform(0.05, 0.10))
            
            # Send ingestion POST request
            data_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{base_url}/api/predictions/telemetry",
                data=data_bytes,
                headers={'Content-Type': 'application/json'}
            )
            
            with opener.open(req) as res:
                body = res.read().decode('utf-8')
                res_json = json.loads(body)
                
                # Capture receipt time immediately
                receipt_time = time.time()
                
                e2e_ms = (receipt_time - source_time) * 1000.0
                e2e_latencies.append(e2e_ms)
                
                ingestion_latencies.append(res_json["latencies_ms"]["ingestion_ms"])
                inference_latencies.append(res_json["latencies_ms"]["inference_ms"])
                api_latencies.append(res_json["latencies_ms"]["api_response_ms"])
                
                print(f"  Run {i+1:02d}: E2E Latency = {e2e_ms:.2f} ms | Model Prob = {res_json['probability']:.2f}")                
        # Calculate statistics
        print("\n--- Latency Statistics (N = 15 events) ---")
        stats = {
            "Min": np.min(e2e_latencies),
            "Max": np.max(e2e_latencies),
            "Mean": np.mean(e2e_latencies),
            "Median": np.median(e2e_latencies),
            "P95": np.percentile(e2e_latencies, 95),
            "StdDev": np.std(e2e_latencies)
        }
        for k, v in stats.items():
            print(f"  - {k}: {v:.2f} ms")            
        # Draw and save latency visualization
        print("\nGenerating latency plots...")
        import matplotlib.pyplot as plt        
        plt.figure(figsize=(10, 5))
        plt.plot(range(1, num_events+1), e2e_latencies, marker='o', color='crimson', linewidth=2, label='End-to-End Latency')
        plt.plot(range(1, num_events+1), ingestion_latencies, marker='s', color='orange', linestyle='--', label='Ingestion Delay')
        plt.plot(range(1, num_events+1), inference_latencies, marker='^', color='teal', linestyle=':', label='Inference Execution')        
        plt.title('ClimateTwin Telemetry Pipeline Latencies (N=15 Events)')
        plt.xlabel('Simulated Test Run')
        plt.ylabel('Latency (ms)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()       
        plots_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\docs\plots"
        os.makedirs(plots_dir, exist_ok=True)
        plt.savefig(os.path.join(plots_dir, 'phase7_latency.png'))
        plt.close()
        print("Plot successfully saved to docs/plots/phase7_latency.png")
    except Exception as e:
        print("\n!!! TEST FAILED !!!")
        print(e)
        failed = True
    finally:
        print("\nStopping FastAPI backend...")
        proc.terminate()
        proc.wait()        
    # Write statistical summary file for integration verification
    if not failed:
        stats_path = os.path.join(r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\docs", "latency_stats.json")
        with open(stats_path, "w") as f_out:
            json.dump({
                "test_events": num_events,
                "stats_ms": {k: float(v) for k, v in stats.items()},
                "raw_e2e_ms": [float(x) for x in e2e_latencies]
            }, f_out, indent=2)
        print("=== ALL LATENCY TESTS COMPLETED SUCCESSFULLY ===")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_phase7_validation()
