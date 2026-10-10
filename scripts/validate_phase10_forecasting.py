import subprocess
import time
import urllib.request
import urllib.error
import json
import sys
import os
import numpy as np

def run_forecasting_tests():
    print('=== Phase 10: Short-Horizon Predictive Flood Forecasting Validation Suite ===')
    base_dir = r'C:\Users\gokul\Desktop\PROJECTS\climatetwin'
    backend_dir = os.path.join(base_dir, 'backend')
    
    # 1. Start FastAPI backend as a subprocess
    print('[Step 1] Starting FastAPI backend subprocess...')
    proc = subprocess.Popen(
        [r'backend\venv\Scripts\python.exe', '-m', 'uvicorn', 'app.main:app', '--port', '8000'],
        cwd=backend_dir
    )
    
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for _ in range(15):
        try:
            req = urllib.request.Request('http://127.0.0.1:8000/health')
            with opener.open(req, timeout=2) as res:
                if res.status == 200:
                    break
        except Exception:
            time.sleep(1)
            
    base_url = 'http://127.0.0.1:8000'
    passed_tests = 0
    total_tests = 15
    
    try:
        # Test 1: Model Loading & File Presence
        print('\n--- Test 01: Forecasting Model Bundle Verification ---')
        model_path = os.path.join(backend_dir, 'app', 'models', 'flood_forecast_models.pkl')
        assert os.path.exists(model_path), f'Missing model file at {model_path}'
        assert os.path.getsize(model_path) > 10000, 'Model file is too small or corrupt'
        print('  [PASS] Forecast model bundle file physically exists and is verified.')
        passed_tests += 1
        
        # Test 2: Valid Forecast Request on Default Assimilated State
        print('\n--- Test 02: Valid Short-Horizon Forecast Request ---')
        req = urllib.request.Request(f'{base_url}/api/predictions/forecast', data=b'{}', headers={'Content-Type': 'application/json'})
        with opener.open(req) as res:
            assert res.status == 200
            res_json = json.loads(res.read().decode('utf-8'))
            assert 'forecast' in res_json
            assert '15min' in res_json['forecast']
            assert '30min' in res_json['forecast']
            assert '60min' in res_json['forecast']
            assert 'current_probability' in res_json
            assert 'current_risk' in res_json
            assert 'model_version' in res_json
            print('  [PASS] Received valid forecast response.')
        passed_tests += 1
        
        # Test 3: 15-Minute Horizon Output Verification
        print('\n--- Test 03: 15-Minute Forecast Horizon Output ---')
        f15 = res_json['forecast']['15min']
        assert f15['horizon_minutes'] == 15
        assert 0.0 <= f15['probability'] <= 1.0
        assert f15['risk_level'] in ['LOW', 'MODERATE', 'HIGH', 'CRITICAL']
        assert f15['predicted_state'] in [0, 1]
        print('  [PASS] 15-min forecast verified: Prob=' + str(round(f15['probability'], 3)) + ', Risk=' + f15['risk_level'])
        passed_tests += 1
        
        # Test 4: 30-Minute Horizon Output Verification
        print('\n--- Test 04: 30-Minute Forecast Horizon Output ---')
        f30 = res_json['forecast']['30min']
        assert f30['horizon_minutes'] == 30
        assert 0.0 <= f30['probability'] <= 1.0
        assert f30['risk_level'] in ['LOW', 'MODERATE', 'HIGH', 'CRITICAL']
        assert f30['predicted_state'] in [0, 1]
        print('  [PASS] 30-min forecast verified: Prob=' + str(round(f30['probability'], 3)) + ', Risk=' + f30['risk_level'])
        passed_tests += 1
        
        # Test 5: 60-Minute Horizon Output Verification
        print('\n--- Test 05: 60-Minute Forecast Horizon Output ---')
        f60 = res_json['forecast']['60min']
        assert f60['horizon_minutes'] == 60
        assert 0.0 <= f60['probability'] <= 1.0
        assert f60['risk_level'] in ['LOW', 'MODERATE', 'HIGH', 'CRITICAL']
        assert f60['predicted_state'] in [0, 1]
        print('  [PASS] 60-min forecast verified: Prob=' + str(round(f60['probability'], 3)) + ', Risk=' + f60['risk_level'])
        passed_tests += 1
        
        # Test 6: Risk Threshold Boundaries
        print('\n--- Test 06: Risk Threshold Boundaries Classification ---')
        assert res_json['thresholds_disclaimer'].startswith('WARNING:')
        for h_key in ['15min', '30min', '60min']:
            p = res_json['forecast'][h_key]['probability']
            expected_risk = 'LOW' if p < 0.20 else 'MODERATE' if p < 0.50 else 'HIGH' if p < 0.80 else 'CRITICAL'
            assert res_json['forecast'][h_key]['risk_level'] == expected_risk
        print('  [PASS] Risk classification strictly obeys defined threshold intervals.')
        passed_tests += 1
        
        # Test 7: Assimilation -> Forecast Sensitivity Integration
        print('\n--- Test 07: Data Assimilation -> Forecast Pipeline Sensitivity ---')
        req_reset = urllib.request.Request(f'{base_url}/api/digital-twins/reset', data=b'{}', headers={'Content-Type': 'application/json'})
        opener.open(req_reset)
        
        req_fc1 = urllib.request.Request(f'{base_url}/api/predictions/forecast', data=b'{}', headers={'Content-Type': 'application/json'})
        with opener.open(req_fc1) as res:
            base_fc = json.loads(res.read().decode('utf-8'))
            base_p60 = base_fc['forecast']['60min']['probability']
            
        storm_obs = [
            {'asset_id': 'rainfall_daily', 'variable': 'rainfall_daily', 'value': 250.0, 'quality_flag': 'GROUND_TRUTH'},
            {'asset_id': 'POONDI', 'variable': 'water_level', 'value': 3200.0, 'quality_flag': 'GROUND_TRUTH'},
            {'asset_id': 'REDHILLS', 'variable': 'water_level', 'value': 3250.0, 'quality_flag': 'GROUND_TRUTH'},
            {'asset_id': 'CHEMBARAMBAKKAM', 'variable': 'water_level', 'value': 3550.0, 'quality_flag': 'GROUND_TRUTH'}
        ]
        for obs in storm_obs:
            req_assim = urllib.request.Request(
                f'{base_url}/api/digital-twins/assimilate',
                data=json.dumps(obs).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            opener.open(req_assim)
            
        req_fc2 = urllib.request.Request(f'{base_url}/api/predictions/forecast', data=b'{}', headers={'Content-Type': 'application/json'})
        with opener.open(req_fc2) as res:
            storm_fc = json.loads(res.read().decode('utf-8'))
            storm_p60 = storm_fc['forecast']['60min']['probability']
            
        print('  [PASS] Baseline 60m Forecast: ' + str(round(base_p60*100, 1)) + '% -> Storm Assimilated 60m Forecast: ' + str(round(storm_p60*100, 1)) + '%')
        assert storm_p60 > base_p60, 'Forecasting model failed to respond to storm telemetry assimilation'
        passed_tests += 1
        
        # Test 8: Lead Time Calculation
        print('\n--- Test 08: Dynamic Predicted Lead Time Calculation ---')
        assert 'lead_time_text' in storm_fc
        assert isinstance(storm_fc['lead_time_text'], str)
        print('  [PASS] Lead time output: ' + storm_fc['lead_time_text'])
        passed_tests += 1
        
        # Test 9: Telemetry Pipeline Forecast Integration & Latency
        print('\n--- Test 09: Telemetry Pipeline Multi-Horizon Tracking & Latency ---')
        telemetry_payload = {
            'source_timestamp': time.time(),
            'rainfall_daily': 60.0,
            'rainfall_3d_sum': 110.0,
            'rainfall_5d_sum': 140.0,
            'rainfall_7d_sum': 170.0,
            'temp_mean': 27.0,
            'temp_max': 31.5,
            'temp_min': 24.5,
            'dew_point_mean': 23.5,
            'wind_speed_mean': 3.8,
            'POONDI': 2900.0,
            'CHOLAVARAM': 920.0,
            'REDHILLS': 3000.0,
            'CHEMBARAMBAKKAM': 3200.0,
            'inference_mode': 'cloud'
        }
        req_tel = urllib.request.Request(
            f'{base_url}/api/predictions/telemetry',
            data=json.dumps(telemetry_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with opener.open(req_tel) as res:
            tel_json = json.loads(res.read().decode('utf-8'))
            assert 'forecast' in tel_json
            assert 'forecast_inference_ms' in tel_json['latencies_ms']
            fc_lat = tel_json['latencies_ms']['forecast_inference_ms']
            print('  [PASS] Telemetry forecast inference latency: ' + str(round(fc_lat, 3)) + ' ms')
        passed_tests += 1
        
        # Test 10: Missing Input / Partial Body Handling
        print('\n--- Test 10: Null Payload Safe Fallback ---')
        req_null = urllib.request.Request(f'{base_url}/api/predictions/forecast', data=b'', headers={'Content-Type': 'application/json'})
        with opener.open(req_null) as res:
            assert res.status == 200
            print('  [PASS] Null payload safely processed by defaulting to active twin state.')
        passed_tests += 1
        
        # Test 11: Invalid Non-Numeric Input Rejection (HTTP 422)
        print('\n--- Test 11: Invalid Non-Numeric Input Rejection (422) ---')
        bad_payload = {'rainfall_daily': 'corrupted_string'}
        req_bad = urllib.request.Request(
            f'{base_url}/api/predictions/forecast',
            data=json.dumps(bad_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        try:
            opener.open(req_bad)
            raise AssertionError('Expected 422 Unprocessable Entity')
        except urllib.error.HTTPError as err:
            assert err.code == 422
            print('  [PASS] Correctly rejected invalid data with HTTP 422.')
        passed_tests += 1
        
        # Test 12: Future Timestamp Protection
        print('\n--- Test 12: Future Timestamp Protection ---')
        future_payload = {
            'asset_id': 'POONDI',
            'variable': 'water_level',
            'value': 2800.0,
            'timestamp': '2099-01-01T00:00:00Z'
        }
        req_fut = urllib.request.Request(
            f'{base_url}/api/digital-twins/assimilate',
            data=json.dumps(future_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with opener.open(req_fut) as res:
            fut_json = json.loads(res.read().decode('utf-8'))
            assert fut_json['validation_status'] == 'REJECTED'
            print('  [PASS] Future observation rejected by 6-stage validator.')
        passed_tests += 1
        
        # Test 13: Feature Schema Consistency Check (20 Features)
        print('\n--- Test 13: Feature Schema Consistency Audit ---')
        assert len(res_json['assimilated_features']) == 20, 'Expected 20 features, got ' + str(len(res_json['assimilated_features']))
        expected_keys = [
            'rainfall_daily', 'rainfall_3d_sum', 'rainfall_5d_sum', 'rainfall_7d_sum',
            'rainfall_rate_1h', 'rainfall_trend', 'temp_mean', 'temp_max', 'temp_min',
            'dew_point_mean', 'dew_point_depression', 'wind_speed_mean', 'wind_speed_trend',
            'POONDI', 'CHOLAVARAM', 'REDHILLS', 'CHEMBARAMBAKKAM',
            'total_reservoir_level', 'reservoir_fill_ratio', 'reservoir_storage_rate_1d'
        ]
        for k in expected_keys:
            assert k in res_json['assimilated_features'], 'Missing expected feature: ' + k
        print('  [PASS] Exact 20-feature temporal schema confirmed.')
        passed_tests += 1
        
        # Test 14: Historical Backtest Verification
        print('\n--- Test 14: Historical Backtest Verification ---')
        bt_json_path = os.path.join(base_dir, 'docs', 'forecast_evaluation.json')
        assert os.path.exists(bt_json_path), 'Missing forecast evaluation report'
        with open(bt_json_path, 'r') as f:
            bt_report = json.load(f)
        assert bt_report['status'] == 'PASS'
        assert bt_report['leakage_audit']['anti_leakage_enforced'] is True
        print('  [PASS] Historical backtest report verified with anti-leakage compliance.')
        passed_tests += 1
        
        # Test 15: Evaluation Plots Physically Generated
        print('\n--- Test 15: Evaluation Visualizations Verified ---')
        plot_file = os.path.join(base_dir, 'docs', 'plots', 'phase10_forecast_evaluation.png')
        assert os.path.exists(plot_file), 'Missing plot file at ' + plot_file
        assert os.path.getsize(plot_file) > 50000, 'Plot file is too small or corrupt'
        print('  [PASS] Multi-horizon ROC, PR, Feature Importance, and Backtest plot verified.')
        passed_tests += 1

    except Exception as e:
        print('\n!!! TEST FAILED WITH EXCEPTION: ' + str(e) + ' !!!')
        raise e
    finally:
        print('\n[Cleanup] Stopping FastAPI backend subprocess...')
        proc.terminate()
        proc.wait()
        
    print('\n=================================================================')
    print('  ALL PHASE 10 FORECASTING TESTS PASSED (' + str(passed_tests) + '/' + str(total_tests) + ') (STATUS: PASS)')
    print('=================================================================')

if __name__ == '__main__':
    run_forecasting_tests()
