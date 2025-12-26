import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test API key for testing
TEST_API_KEY = "test-api-key-for-testing-12345"


@pytest.fixture(scope="function")  
def mock_redis_connection():
    """Mock Redis connection for all tests."""
    mock_conn = MagicMock()
    mock_conn.ping.return_value = True
    mock_conn.get.return_value = None
    mock_conn.set.return_value = True
    return mock_conn


@pytest.fixture(scope="function")
def mock_queue():
    """Mock RQ queue."""
    mock_q = MagicMock()
    mock_job = MagicMock()
    mock_job.id = "test-job-id-123"
    mock_q.enqueue.return_value = mock_job
    return mock_q


@pytest.fixture(scope="function")
def client(mock_redis_connection, mock_queue):
    """Test client with mocked Redis."""
    # Create mock redis client instance
    mock_redis_instance = MagicMock()
    mock_redis_instance.is_connected.return_value = True
    mock_redis_instance.connection = mock_redis_connection
    mock_redis_instance.queue = mock_queue
    
    with patch("app.core.redis_client.RedisClient") as MockRedisClient:
        MockRedisClient.return_value = mock_redis_instance
        
        with patch("app.core.redis_client.redis_client", mock_redis_instance):
            with patch("app.api.v1.routes.redis_client", mock_redis_instance):
                with patch("app.services.job_service.redis_client", mock_redis_instance):
                    from app.main import create_app
                    app = create_app()
                    with TestClient(app) as test_client:
                        yield test_client


@pytest.fixture
def api_key_header():
    """Return headers with valid test API key."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def sample_image():
    """Create a minimal valid PNG byte content."""
    # Minimal 1x1 transparent PNG
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 pixels
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
        0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
        0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
        0x42, 0x60, 0x82
    ])


@pytest.fixture  
def sample_pdf():
    """Create a minimal valid PDF byte content."""
    # Minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
196
%%EOF"""
    return pdf_content
