import os
import sys
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

def run_validation():
    print("========================================")
    print("PHASE 18 VALIDATION: Explainable AI")
    print("========================================")
    
    url = "http://127.0.0.1:8000/api/explainability/HEATWAVE"
    print(f"\n[1] Testing {url}")
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            print("✅ Success! API returned 200 OK.")
            data = res.json()
            
            print("\n[2] Checking Explainability Structure")
            keys = ['risk_level', 'risk_score', 'dominant_drivers', 'protective_factors', 
                    'trend', 'confidence_score', 'data_quality', 'affected_assets', 
                    'recommended_priorities', 'explanation', 'changes', 'provenance']
            missing = [k for k in keys if k not in data]
            if not missing:
                print("✅ All required keys present in JSON response.")
            else:
                print(f"❌ Missing keys: {missing}")
                
            print("\n[3] Checking Drivers & Protective Factors")
            if data['dominant_drivers'] or data['protective_factors']:
                print(f"✅ Found {len(data['dominant_drivers'])} drivers and {len(data['protective_factors'])} protective factors.")
            else:
                print("❌ No drivers or protective factors found.")
                
            print("\n[4] Checking Change Intelligence")
            if data['changes']:
                print(f"✅ Found {len(data['changes'])} change intelligence records.")
            else:
                print("❌ No change intelligence found.")
                
            print("\n[5] Checking Trend Detection")
            if data['trend'] in ["INCREASING", "STABLE", "DECREASING"]:
                print(f"✅ Trend classification valid: {data['trend']}")
            else:
                print(f"❌ Invalid trend: {data['trend']}")
                
            print("\n[6] Checking Text Explanation")
            if data['explanation']:
                print(f"✅ Explanation generated: '{data['explanation']}'")
            else:
                print("❌ Missing text explanation.")
                
        else:
            print(f"❌ API Error: {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        
    print("\nValidation complete.")

if __name__ == '__main__':
    run_validation()
