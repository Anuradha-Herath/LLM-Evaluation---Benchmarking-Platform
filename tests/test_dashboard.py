import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_ui_endpoint():
    """Test /dashboard route returns 200 OK HTML web page."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "LLM Evaluation & Benchmarking Platform" in response.text
    assert "Overview" in response.text
    assert "Model Comparison" in response.text


def test_api_v1_dashboard_ui_endpoint():
    """Test /api/v1/dashboard route returns 200 OK HTML web page."""
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "LLM Evaluation & Benchmarking Platform" in response.text
