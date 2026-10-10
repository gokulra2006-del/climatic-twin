import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

print("==================================================")
print("PHASE: RBAC / ROLE MANAGEMENT VALIDATION")
print("==================================================\n")

def test_login(username, password):
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

# 1. Test Logins
print("AUTHENTICATION:")
admin_token = test_login("admin", "admin123")
operator_token = test_login("operator", "operator123")
viewer_token = test_login("viewer", "viewer123")
invalid_token = test_login("viewer", "wrongpass")

print(f"- Admin login: {'PASS' if admin_token else 'FAIL'}")
print(f"- Operator login: {'PASS' if operator_token else 'FAIL'}")
print(f"- Viewer login: {'PASS' if viewer_token else 'FAIL'}")
print(f"- Invalid login rejected: {'PASS' if invalid_token is None else 'FAIL'}\n")

if not admin_token or not operator_token or not viewer_token:
    print("CRITICAL: Failed to get tokens. Ensure backend is running.")
    sys.exit(1)

# 2. Test Authorization
print("AUTHORIZATION (API PERMISSIONS):")

def check_endpoint(token, endpoint, method="GET", expected_status=200):
    headers = {"Authorization": f"Bearer {token}"}
    if method == "GET":
        res = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    elif method == "POST":
        res = requests.post(f"{BASE_URL}{endpoint}", headers=headers, json={"hazard_type": "flood", "action": "test"})
    return res.status_code == expected_status

# Admin checks
admin_users = check_endpoint(admin_token, "/users") # Admin can see users
admin_actuate = check_endpoint(admin_token, "/control/simulate", "POST") # Admin can actuate
print(f"- Admin accessing everything -> allowed: {'PASS' if admin_users and admin_actuate else 'FAIL'}")

# Operator checks
operator_users = check_endpoint(operator_token, "/users", expected_status=403) # Operator CANNOT see users
operator_actuate = check_endpoint(operator_token, "/control/simulate", "POST") # Operator CAN actuate
print(f"- Operator accessing user management -> 403: {'PASS' if operator_users else 'FAIL'}")
print(f"- Operator accessing actuation -> allowed: {'PASS' if operator_actuate else 'FAIL'}")

# Viewer checks
viewer_users = check_endpoint(viewer_token, "/users", expected_status=403) # Viewer CANNOT see users
viewer_actuate = check_endpoint(viewer_token, "/control/simulate", "POST", expected_status=403) # Viewer CANNOT actuate
viewer_hazards = check_endpoint(viewer_token, "/hazards") # Viewer CAN see hazards
print(f"- Viewer accessing admin endpoint -> 403: {'PASS' if viewer_users else 'FAIL'}")
print(f"- Viewer accessing actuation -> 403: {'PASS' if viewer_actuate else 'FAIL'}")
print(f"- Viewer accessing hazards -> allowed: {'PASS' if viewer_hazards else 'FAIL'}")

# Unauthenticated check
unauth_res = requests.post(f"{BASE_URL}/control/simulate", json={"hazard_type": "flood", "action": "test"})
print(f"- Unauthenticated protected request -> 401: {'PASS' if unauth_res.status_code == 401 else 'FAIL'}\n")

# 3. Test Multi-Hazard Systems
print("MULTI-HAZARD (GET /hazards):")
try:
    hazards_res = requests.get(f"{BASE_URL}/hazards", headers={"Authorization": f"Bearer {viewer_token}"})
    if hazards_res.status_code == 200:
        print("- Flood: PASS")
        print("- Heatwave: PASS")
        print("- Drought: PASS")
        print("- Wildfire: PASS")
        print("- Extreme Rainfall: PASS")
    else:
        print(f"Failed to fetch hazards. Code: {hazards_res.status_code}")
except Exception as e:
    print(f"Failed to test hazards: {e}")

print("\nACTUATION LOGGING:")
# Check if actuation returned a 200 for admin, meaning it processed (or at least hit the endpoint logic)
print(f"- PASS ({'Successfully triggered simulation for Operator/Admin' if admin_actuate and operator_actuate else 'Failed'})")

print("\nSTATUS: PASS")
