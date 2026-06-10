import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "logistics-ai-optimizer", "version": "2.1.0"}

def test_mock_orders():
    response = client.get("/mock-orders")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "id" in data[0]

def test_optimize_endpoint():
    # Test bypassing the 15 node limit with 20 mock orders
    orders = [{"id": f"O{i}", "lat": 12.0, "lng": 77.0, "weight": 2.0, "priority": 5} for i in range(20)]
    response = client.post("/optimize", json={"orders": orders})
    assert response.status_code == 200
    data = response.json()
    assert "vans" in data
    assert len(data["vans"]) > 0
    assert data["total_orders"] == 20
