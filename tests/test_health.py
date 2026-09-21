def test_root_health_endpoint(client):
    """Test standard root /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "LLM Evaluation & Benchmarking Platform"
    assert "version" in data


def test_api_v1_health_endpoint(client):
    """Test API v1 /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["environment"] is not None
