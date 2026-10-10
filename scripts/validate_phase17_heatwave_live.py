import os
import sys
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

def run_validation():
    print("========================================")
    print("PHASE 17 VALIDATION: Heatwave Live Data")
    print("========================================")
    
    url = "http://127.0.0.1:8000/api/hazards/HEATWAVE/predictions"
    print(f"\n[1] Testing {url}")
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            print("✅ Success! API returned 200 OK.")
            data = res.json()
            
            print(f"Risk Level: {data.get('risk_level')}")
            print(f"Probability: {data.get('probability')}")
            
            metrics = data.get('forecast_metrics', {})
            print(f"\n[2] Checking Forecast Metrics")
            if metrics:
                print(f"✅ Found forecast metrics: Peak Temp: {metrics.get('peak_temp')}, Peak Heat Index: {metrics.get('peak_heat_index')}, Early Warning: {metrics.get('early_warning_status')}")
            else:
                print("❌ Missing forecast metrics!")
                
            trend = data.get('trend_48h', [])
            print(f"\n[3] Checking Trend 48h Array")
            if trend:
                print(f"✅ Found trend_48h array with length: {len(trend)}")
            else:
                print("❌ Missing trend_48h array!")
        else:
            print(f"❌ API Error: {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        
    print("\nValidation complete.")

if __name__ == '__main__':
    run_validation()
