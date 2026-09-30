import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import init_db, engine
from sqlalchemy import inspect


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database tables are initialized for testing."""
    init_db()


@pytest.fixture
def client():
    """Test client fixture."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Test the root welcoming endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert "version" in data
    assert data["health_check"] == "/api/v1/health"


def test_health_check_endpoint(client):
    """Test the system health check and database connectivity."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "version" in data
    assert "environment" in data
    assert "llm_provider" in data


def test_database_tables_created():
    """Verify that all core schema tables have been created in the database."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    expected_tables = {
        "jobs",
        "candidates",
        "resumes",
        "profiles",
        "requirements",
        "scores",
        "skill_gaps",
        "recommendations",
    }
    for table in expected_tables:
        assert table in table_names, f"Table '{table}' should be present in database schema"
