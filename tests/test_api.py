"""Integration tests for the REST API endpoints."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from PIL import Image

from fastapi.testclient import TestClient

from app.main import app
from app.auth.service import require_auth


@pytest.fixture
def client():
    """Create a test client with auth bypassed."""
    app.dependency_overrides[require_auth] = lambda: "test_user"
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_image_bytes(tmp_path: Path) -> tuple[Path, bytes]:
    """Create a sample JPEG image and return its path and bytes."""
    img = Image.new("RGB", (224, 224), color=(100, 150, 200))
    path = tmp_path / "test.jpg"
    img.save(str(path), "JPEG")
    return path, path.read_bytes()


class TestHealthEndpoint:
    def test_health(self, client: TestClient):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestClassifyEndpoint:
    def test_classify_image(self, client: TestClient, sample_image_bytes):
        path, data = sample_image_bytes
        resp = client.post(
            "/api/classify",
            files={"file": ("car.jpg", data, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "predicted_class" in body
        assert "confidence" in body
        assert "imagenet_label" in body
        assert 0.0 <= body["confidence"] <= 1.0

    def test_classify_rejects_non_image(self, client: TestClient):
        resp = client.post(
            "/api/classify",
            files={"file": ("test.txt", b"not an image", "text/plain")},
        )
        assert resp.status_code == 400


class TestAskEndpoint:
    @patch("app.api.routes.agent")
    def test_ask_returns_structure(self, mock_agent, client: TestClient):
        """Verify the response structure (mocking LLM)."""
        from app.agent.service import AgentResponse

        mock_agent.execute = AsyncMock(
            return_value=AgentResponse(
                question="test",
                generated_sql="SELECT 1",
                results=[{"vehicle_id": 1, "brand": "Toyota"}],
                row_count=1,
            )
        )

        resp = client.post("/api/ask", json={"question": "test"})
        assert resp.status_code == 200
        body = resp.json()
        assert "question" in body
        assert "generated_sql" in body
        assert "results" in body
        assert "row_count" in body

    def test_ask_empty_question(self, client: TestClient):
        """Empty question should return 422 (validation error)."""
        resp = client.post("/api/ask", json={"question": ""})
        assert resp.status_code == 422

    def test_ask_whitespace_question(self, client: TestClient):
        """Whitespace-only question should return 422 (validation error)."""
        resp = client.post("/api/ask", json={"question": "   "})
        assert resp.status_code == 422


class TestWebUI:
    def test_index_page(self, client: TestClient):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Vehicle ML Agent" in resp.text
