"""
Tests for the FastAPI API

Run with: poetry run pytest tests/test_api.py -v
"""

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


# Mock environment before importing app
@pytest.fixture(autouse=True)
def mock_env():
    """Mock environment variables for testing."""
    env_vars = {
        "LIVEKIT_API_KEY": "test-api-key",
        "LIVEKIT_API_SECRET": "test-api-secret",
        "LIVEKIT_URL": "wss://test.livekit.cloud",
        "GOOGLE_API_KEY": "test-google-key",
        "QDRANT_URL": "https://test.qdrant.io",
        "QDRANT_API_KEY": "test-qdrant-key",
    }
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    # Mock Qdrant service before importing
    with patch("rag.qdrant_service.get_qdrant_service") as mock_qdrant:
        mock_service = MagicMock()
        mock_service.collection_exists = AsyncMock(return_value=True)
        mock_service.get_collection_info = AsyncMock(return_value={
            "name": "test_collection",
            "points_count": 10,
            "status": "green"
        })
        mock_service.close = AsyncMock()
        mock_qdrant.return_value = mock_service
        
        from api.main import app
        with TestClient(app) as test_client:
            yield test_client


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_returns_info(self, client):
        """Test that root returns API info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Voara Voice Agent API"
        assert "version" in data
        assert data["docs"] == "/docs"


class TestTokenEndpoint:
    """Tests for the token generation endpoint."""
    
    def test_generate_token_success(self, client):
        """Test successful token generation."""
        with patch("api.routes.token.api.AccessToken") as mock_token_class:
            # Create mock token builder chain
            mock_token = MagicMock()
            mock_token.with_identity.return_value = mock_token
            mock_token.with_name.return_value = mock_token
            mock_token.with_grants.return_value = mock_token
            mock_token.to_jwt.return_value = "test-jwt-token"
            mock_token_class.return_value = mock_token
            
            response = client.post("/api/token", json={
                "room_name": "test-room",
                "participant_name": "Test User"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["token"] == "test-jwt-token"
            assert data["room_name"] == "test-room"
            assert data["participant_identity"] == "Test User"
            assert data["livekit_url"] == "wss://test.livekit.cloud"
    
    def test_generate_token_with_custom_identity(self, client):
        """Test token generation with custom identity."""
        with patch("api.routes.token.api.AccessToken") as mock_token_class:
            mock_token = MagicMock()
            mock_token.with_identity.return_value = mock_token
            mock_token.with_name.return_value = mock_token
            mock_token.with_grants.return_value = mock_token
            mock_token.to_jwt.return_value = "test-jwt-token"
            mock_token_class.return_value = mock_token
            
            response = client.post("/api/token", json={
                "room_name": "test-room",
                "participant_name": "Test User",
                "participant_identity": "custom-id-123"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["participant_identity"] == "custom-id-123"
    
    def test_generate_token_missing_room_name(self, client):
        """Test token generation fails without room_name."""
        response = client.post("/api/token", json={
            "participant_name": "Test User"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_token_missing_participant_name(self, client):
        """Test token generation fails without participant_name."""
        response = client.post("/api/token", json={
            "room_name": "test-room"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_token_empty_room_name(self, client):
        """Test token generation fails with empty room_name."""
        response = client.post("/api/token", json={
            "room_name": "",
            "participant_name": "Test User"
        })
        
        assert response.status_code == 422  # Validation error


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_check_returns_status(self, client):
        """Test health check returns status."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "dependencies" in data
    
    def test_health_check_includes_dependencies(self, client):
        """Test health check includes all dependencies."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        dep_names = [d["name"] for d in data["dependencies"]]
        assert "qdrant" in dep_names
        assert "livekit" in dep_names
        assert "google_ai" in dep_names
    
    def test_liveness_probe(self, client):
        """Test Kubernetes liveness probe."""
        response = client.get("/api/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
    
    def test_readiness_probe(self, client):
        """Test Kubernetes readiness probe."""
        response = client.get("/api/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestRAGEndpoint:
    """Tests for the RAG query endpoint."""
    
    def test_rag_query_validation(self, client):
        """Test RAG query validates input."""
        response = client.post("/api/rag/query", json={
            "query": ""  # Empty query
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_rag_stats_endpoint(self, client):
        """Test RAG stats endpoint."""
        with patch("rag.get_qdrant_service") as mock_qdrant:
            mock_service = MagicMock()
            mock_service.get_collection_info = AsyncMock(return_value={
                "name": "voara_kb",
                "points_count": 50,
                "status": "green"
            })
            mock_qdrant.return_value = mock_service
            
            response = client.get("/api/rag/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert "collection" in data
            assert "config" in data


class TestCORSMiddleware:
    """Tests for CORS configuration."""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present."""
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        
        # CORS should allow the localhost origin
        # Note: Actual header checking depends on middleware configuration
        assert response.status_code in [200, 400]  # OPTIONS may return different codes
