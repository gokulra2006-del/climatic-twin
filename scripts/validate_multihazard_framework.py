import requests
import json
import sys

API_URL = "http://localhost:8000"

def test_flood_apis_preserved():
    print("Testing existing flood APIs...")
    try:
        res = requests.get(f"{API_URL}/api/predictions/latest")
        if res.status_code != 200:
            print(f"FAIL: /api/predictions/latest returned {res.status_code}")
            return False
            
        data = res.json()
        if "risk_level" not in data or "probability" not in data:
            print("FAIL: Flood prediction payload is corrupted.")
            return False
            
        res_assets = requests.get(f"{API_URL}/api/assets/")
        if res_assets.status_code != 200:
            print("FAIL: /api/assets/ is broken.")
            return False
            
        print("PASS: Existing flood APIs are functioning.")
        return True
    except Exception as e:
        print(f"FAIL: Exception connecting to flood APIs: {e}")
        return False

def test_hazard_registry():
    print("Testing multi-hazard registry API...")
    try:
        res = requests.get(f"{API_URL}/api/hazards/types")
        if res.status_code != 200:
            print(f"FAIL: /api/hazards/types returned {res.status_code}")
            return False
            
        types = res.json()
        names = [t["name"] for t in types]
        expected = ["FLOOD", "HEATWAVE", "DROUGHT", "WILDFIRE", "EXTREME_RAINFALL"]
        
        for e in expected:
            if e not in names:
                print(f"FAIL: Missing hazard type {e}")
                return False
                
        # Verify Flood is IMPLEMENTED and others are FRAMEWORK READY
        for t in types:
            if t["name"] == "FLOOD" and t["status"] != "IMPLEMENTED":
                print(f"FAIL: Flood status is {t['status']}, should be IMPLEMENTED")
                return False
            if t["name"] != "FLOOD" and t["status"] != "FRAMEWORK READY":
                print(f"FAIL: {t['name']} status is {t['status']}, should be FRAMEWORK READY")
                return False
                
        print("PASS: Multi-hazard registry is valid.")
        return True
    except Exception as e:
        print(f"FAIL: Exception connecting to hazard types API: {e}")
        return False

def test_future_hazard_routes():
    print("Testing generic routing for future hazards...")
    try:
        res = requests.get(f"{API_URL}/api/hazards/HEATWAVE/predictions")
        if res.status_code != 200:
            print("FAIL: Generic routing failed.")
            return False
            
        data = res.json()
        if data.get("status") != "FRAMEWORK READY":
            print("FAIL: Heatwave did not return FRAMEWORK READY status.")
            return False
            
        print("PASS: Future hazard routing works properly.")
        return True
    except Exception as e:
        print(f"FAIL: Exception during future hazard route testing: {e}")
        return False

def main():
    success = True
    
    if not test_flood_apis_preserved():
        success = False
        
    if not test_hazard_registry():
        success = False
        
    if not test_future_hazard_routes():
        success = False
        
    if success:
        print("\nSUMMARY: ALL VALIDATIONS PASSED.")
        print("The Multi-Hazard Framework extension has been successfully integrated without breaking existing functionality.")
        sys.exit(0)
    else:
        print("\nSUMMARY: VALIDATION FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
