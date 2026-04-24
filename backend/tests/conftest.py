"""Pytest fixtures for backend tests."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def redis_client():
    """Provide a fake Redis client (fakeredis)."""
    try:
        import fakeredis
        return fakeredis.FakeStrictRedis()
    except ImportError:
        pytest.skip("fakeredis not installed")


@pytest.fixture
def neo4j_driver():
    """Provide a Neo4j driver. Skip if unavailable."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
        driver.verify_connectivity()
        yield driver
        driver.close()
    except Exception:
        pytest.skip("Neo4j not available")


@pytest.fixture
def client():
    """Provide FastAPI TestClient for integration tests."""
    try:
        from backend.main import app
        return TestClient(app)
    except ImportError:
        pytest.skip("FastAPI app not available")
