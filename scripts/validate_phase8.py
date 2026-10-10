import requests
import json
import time

API_URL = "http://localhost:8000/api/v1"
HAZARDS = ["FLOOD", "HEATWAVE", "DROUGHT", "WILDFIRE", "EXTREME_RAINFALL"]

def run_tests():
    results = {
        "status": "INCOMPLETE",
        "hazards": {},
        "compound_risk": "UNTESTED",
        "control_simulation": "UNTESTED",
        "mqtt_status": "UNTESTED"
    }
    
    print("Starting Phase 8 Validation...")
    
    for h in HAZARDS:
        try:
            r = requests.get(f"{API_URL}/hazards/{h}/predictions")
            if r.status_code == 200:
                data = r.json()
                has_uncertainty = "probability_p10" in data and data["probability_p10"] is not None
                has_lead_time = "lead_time_hours" in data
                
                results["hazards"][h] = {
                    "status": "PASS",
                    "has_uncertainty": has_uncertainty,
                    "has_lead_time": has_lead_time,
                    "probability": data.get("probability", -1)
                }
                print(f"[OK] {h} endpoint passed. Uncertainty: {has_uncertainty}, LeadTime: {has_lead_time}")
            else:
                results["hazards"][h] = {"status": "FAIL", "reason": r.text}
                print(f"[FAIL] {h} endpoint failed with status {r.status_code}")
        except Exception as e:
            results["hazards"][h] = {"status": "ERROR", "reason": str(e)}
            print(f"[ERROR] {h} endpoint connection failed")

    # Compound Risk Test
    try:
        r = requests.get(f"{API_URL}/hazards/compound-risk")
        if r.status_code == 200:
            results["compound_risk"] = "PASS"
            print("[OK] Compound risk endpoint passed.")
        else:
            results["compound_risk"] = "FAIL"
            print("[FAIL] Compound risk endpoint failed.")
    except Exception as e:
        results["compound_risk"] = f"ERROR: {str(e)}"
        
    # Control Test
    try:
        payload = {
            "simulation_mode": True,
            "hazard_type": "flood",
            "risk_level": "CRITICAL",
            "risk_probability": 0.95,
            "triggering_features": {}
        }
        r = requests.post(f"{API_URL}/control/simulate", json=payload)
        if r.status_code == 200 and "OPEN_POONDI_FLOODGATE" in r.json().get("command", ""):
            results["control_simulation"] = "PASS"
            print("[OK] Control simulation passed.")
        else:
            results["control_simulation"] = "FAIL"
            print("[FAIL] Control simulation failed.")
    except Exception as e:
        results["control_simulation"] = f"ERROR: {str(e)}"

    results["status"] = "COMPLETE"
    
    with open("../docs/phase8_validation_report.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print("Validation finished. Report written to docs/phase8_validation_report.json")

if __name__ == "__main__":
    run_tests()
