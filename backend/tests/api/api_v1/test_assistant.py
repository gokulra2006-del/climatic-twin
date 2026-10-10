import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_assistant_endpoint_exists():
    response = client.post(
        f"{settings.API_V1_STR}/assistant/chat",
        json={"message": "Hello", "mode": "citizen"}
    )
    # Even if unauthenticated or error, it shouldn't be 404
    assert response.status_code != 404

def test_assistant_valid_question():
    response = client.post(
        f"{settings.API_V1_STR}/assistant/chat",
        json={"message": "What is the flood risk?", "mode": "research"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["mode"] == "research"
    assert "sources" in data
    assert "confidence" in data

def test_assistant_invalid_mode():
    response = client.post(
        f"{settings.API_V1_STR}/assistant/chat",
        json={"message": "Hello", "mode": "hacker"}
    )
    assert response.status_code == 422 # Validation error

def test_assistant_empty_question():
    response = client.post(
        f"{settings.API_V1_STR}/assistant/chat",
        json={"message": "", "mode": "citizen"}
    )
    assert response.status_code == 422 # Min length is 1

def test_assistant_fallback_mode(monkeypatch):
    # Ensure no API key is present for this test
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    response = client.post(
        f"{settings.API_V1_STR}/assistant/chat",
        json={"message": "Test fallback", "mode": "operator"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == "fallback-deterministic"
    assert "deterministic fallback" in data["answer"].lower()
