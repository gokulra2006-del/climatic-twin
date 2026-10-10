import subprocess
import time
import urllib.request
import urllib.error
import json
import sys
def run_tests():
    print("=== Phase 6 Backend & API Integration Tests ===")
    
    # 1. Start FastAPI backend as a subprocess
    print("Starting FastAPI backend...")
    proc = subprocess.Popen(
        [r"backend\venv\Scripts\python.exe", "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\backend"
    )
    
    # Wait for startup
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for _ in range(15):
        try:
            req = urllib.request.Request(f"http://127.0.0.1:8000/health")
            with opener.open(req, timeout=2) as res:
                if res.status == 200:
                    break
        except Exception:
            time.sleep(1)
            
    failed = False
    base_url = "http://127.0.0.1:8000"
    
    try:
        # A. Health check
        print("\nTesting /health endpoint...")
        req = urllib.request.Request(f"{base_url}/health")
        with opener.open(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            print("Status:", response.status)
            print("Response:", res_json)
            assert response.status == 200
            assert res_json["status"] == "healthy"
        
        # B. Assets endpoint
        print("\nTesting /api/assets/ endpoint...")
        req = urllib.request.Request(f"{base_url}/api/assets/")
        with opener.open(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            print("Status:", response.status)
            print("First Asset:", res_json["data"][0])
            assert response.status == 200
            assert len(res_json["data"]) == 4
        
        # C. Latest prediction endpoint
        print("\nTesting /api/predictions/latest endpoint...")
        req = urllib.request.Request(f"{base_url}/api/predictions/latest")
        with opener.open(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            print("Status:", response.status)
            print("Response:", res_json)
            assert response.status == 200
            assert "risk_level" in res_json
        
        # D. Realtime prediction with valid payload
        print("\nTesting /api/predictions/realtime (Valid Input)...")
        payload = {
            "rainfall_daily": 65.5,
            "rainfall_3d_sum": 120.0,
            "rainfall_5d_sum": 150.0,
            "rainfall_7d_sum": 200.0,
            "temp_mean": 27.0,
            "temp_max": 32.0,
            "temp_min": 23.5,
            "dew_point_mean": 24.0,
            "wind_speed_mean": 4.5,
            "POONDI": 3100.0,
            "CHOLAVARAM": 950.0,
            "REDHILLS": 3150.0,
            "CHEMBARAMBAKKAM": 3400.0
        }
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/api/predictions/realtime", 
            data=data_bytes, 
            headers={'Content-Type': 'application/json'}
        )
        with opener.open(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            print("Status:", response.status)
            print("Response:", res_json)
            assert response.status == 200
            assert res_json["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
        
        # E. Invalid prediction payload
        print("\nTesting /api/predictions/realtime (Invalid Input)...")
        bad_payload = {
            "rainfall_daily": "not-a-number",
            "POONDI": 200.0
        }
        data_bytes = json.dumps(bad_payload).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/api/predictions/realtime", 
            data=data_bytes, 
            headers={'Content-Type': 'application/json'}
        )
        try:
            opener.open(req)
            print("!!! TEST FAILED: Allowed invalid input !!!")
            failed = True
        except urllib.error.HTTPError as err:
            print("Status:", err.code)
            print("Response:", err.read().decode('utf-8'))
            assert err.code == 422 # Unprocessable Entity
            print("Pydantic validation error handled correctly (422)!")
        
        # F. Alerts endpoint
        print("\nTesting /api/alerts/ endpoint...")
        req = urllib.request.Request(f"{base_url}/api/alerts/")
        with opener.open(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            print("Status:", response.status)
            print("Response:", res_json["data"])
            assert response.status == 200
            assert len(res_json["data"]) > 0

    except Exception as e:
        print("\n!!! TEST FAILED !!!")
        print(e)
        failed = True
    finally:
        print("\nStopping FastAPI backend...")
        proc.terminate()
        proc.wait()       
    if failed:
        sys.exit(1)
    else:
        print("\n=== ALL BACKEND INTEGRATION TESTS PASSED ===")
if __name__ == "__main__":
    run_tests()