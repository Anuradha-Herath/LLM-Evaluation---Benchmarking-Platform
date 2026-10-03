import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_api_create_evaluation():
    payload = {
        "dataset_path": "datasets/benchmark_v1.json",
        "provider": "mock",
        "model": "mock-api-model",
        "concurrency": 5,
        "persist_db": True,
    }
    response = client.post("/api/v1/evaluations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "run" in data
    assert data["run"]["model"] == "mock-api-model"
    assert data["run"]["passed_cases"] == 50

    run_id = data["run"]["run_id"]

    # Test GET /evaluations/{run_id}
    res_run = client.get(f"/api/v1/evaluations/{run_id}")
    assert res_run.status_code == 200
    assert res_run.json()["run_id"] == run_id

    # Test GET /evaluations/{run_id}/results
    res_results = client.get(f"/api/v1/evaluations/{run_id}/results?limit=5")
    assert res_results.status_code == 200
    assert len(res_results.json()["items"]) == 5

    # Test GET /evaluations/{run_id}/metrics
    res_metrics = client.get(f"/api/v1/evaluations/{run_id}/metrics")
    assert res_metrics.status_code == 200

    # Test GET /evaluations/{run_id}/failures
    res_failures = client.get(f"/api/v1/evaluations/{run_id}/failures")
    assert res_failures.status_code == 200


def test_api_list_evaluations():
    response = client.get("/api/v1/evaluations?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_api_create_benchmark():
    payload = {
        "dataset_path": "datasets/benchmark_v1.json",
        "models": [
            {"provider": "mock", "model": "mock-v1", "label": "Model A"},
            {"provider": "mock", "model": "mock-v2", "label": "Model B"},
        ],
        "concurrency": 5,
    }
    response = client.post("/api/v1/benchmarks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "summary_runs" in data
    assert len(data["summary_runs"]) == 2


def test_api_regression_test():
    payload = {
        "dataset_path": "datasets/benchmark_v1.json",
        "baseline_model": "mock:mock-v1",
        "candidate_model": "mock:mock-v1",
        "limit": 5,
    }
    response = client.post("/api/v1/regression-tests", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("PASS", "FAIL")
    assert "violations" in data


    assert "violations" in data
