from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check_returns_200():
    """Verify that GET /health returns HTTP 200 and expected health metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data
    assert "llm_model" in data
    assert "embedding_model" in data
