import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
from app.core.external_hazards import external_hazards_engine
from starlette.testclient import TestClient
from app.main import app

passed = 0
failed = 0
total = 5

def run_test(num, name, condition, detail=''):
    global passed, failed
    if condition:
        passed += 1
        print(f'[Test {num:02d}] {name}\n  -> PASSED: {detail}')
    else:
        failed += 1
        print(f'[Test {num:02d}] {name}\n  -> FAILED: {detail}')

print('='*65)
print('  CLIMATETWIN PHASE 18: EXTERNAL HAZARDS VALIDATION SUITE')
print('='*65)
print()

async def run_tests():
    # Test 1: Fallback generation
    fallback = external_hazards_engine._generate_fallback_data()
    cond1 = 'hourly' in fallback and len(fallback['hourly']['temperature_2m']) > 0
    run_test(1, 'Synthetic Fallback Data Generation', cond1, 'Generated synthetic hourly data')

    # Test 2: Data Processing
    processed = external_hazards_engine.process_hazard_timeseries(fallback)
    cond2 = 'heat' in processed and 'wind' in processed and 'rainfall' in processed and 'reservoir' in processed
    run_test(2, 'Timeseries Processing', cond2, 'Separated arrays for heat, wind, rainfall, and reservoir')

    # Test 3: Data lengths
    cond3 = len(processed['wind']) == 240
    run_test(3, 'Timeseries Length (10 days hourly)', cond3, f'Wind array has {len(processed["wind"])} points')

    # Test 4: Reservoir Physics
    res = processed['reservoir']
    cond4 = all('volume_mcft' in r and 'fill_percentage' in r for r in res)
    run_test(4, 'Reservoir Physical Simulation', cond4, 'Volume and fill percentages calculated')

    # Test 5: API Endpoint
    client = TestClient(app)
    resp = client.get("/api/external-hazards/detailed")
    cond5 = resp.status_code == 200 and 'metadata' in resp.json()
    run_test(5, 'API GET /api/external-hazards/detailed', cond5, f'Status: {resp.status_code}')

    print()
    print('='*65)
    if failed == 0:
        print(f'  ALL PHASE 18 EXTERNAL HAZARDS TESTS PASSED ({passed}/{total}) (STATUS: PASS)')
    else:
        print(f'  PHASE 18 TESTS: {passed}/{total} PASSED, {failed} FAILED (STATUS: FAIL)')
    print('='*65)

if __name__ == "__main__":
    asyncio.run(run_tests())
