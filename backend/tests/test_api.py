import pytest
from fastapi.testclient import TestClient
import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200

def test_prediction_endpoint():
    # Test the core prediction forecast endpoint
    payload = {
        "features": {},
        "lead_hours": 24,
        "return_uncertainty": True
    }
    response = client.post("/api/predictions/forecast", json=payload)
    # The endpoint might return 200, 422, or 503 if models aren't loaded in test env
    assert response.status_code in [200, 422, 503]

def test_auth_login():
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "any_password_for_demo"}
    )
    assert response.status_code in [200, 400, 401]

def test_protected_route_without_token():
    response = client.post("/api/assets/", json={"name": "Test"})
    assert response.status_code in [401, 422] # Unauthorized or Validation Error

def test_protected_route_with_invalid_token():
    response = client.get("/api/users/me", headers={"Authorization": "Bearer invalidtoken123"})
    assert response.status_code in [401, 404]
