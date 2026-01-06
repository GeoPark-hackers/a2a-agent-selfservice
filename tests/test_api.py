"""Tests for the API routes."""

import pytest
from fastapi.testclient import TestClient

from a2a_selfservice.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


def test_list_agents_empty(client):
    """Test listing agents when none exist."""
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert data["agents"] == []
    assert data["total"] == 0


def test_create_agent(client):
    """Test creating a new agent."""
    agent_definition = {
        "definition": {
            "name": "test-agent",
            "display_name": "Test Agent",
            "description": "A test agent",
            "system_prompt": "You are a helpful test agent.",
            "model": "gpt-4o",
            "tools": [],
            "sub_agents": [],
            "metadata": {},
        },
        "deploy_immediately": False,
    }

    response = client.post("/api/v1/agents", json=agent_definition)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-agent"
    assert data["display_name"] == "Test Agent"
    assert data["status"] == "draft"


def test_get_agent(client):
    """Test getting an agent by name."""
    agent_definition = {
        "definition": {
            "name": "get-test-agent",
            "display_name": "Get Test Agent",
            "description": "An agent for get test",
            "system_prompt": "You are a test agent.",
            "model": "gpt-4o",
            "tools": [],
            "sub_agents": [],
            "metadata": {},
        },
        "deploy_immediately": False,
    }

    client.post("/api/v1/agents", json=agent_definition)

    response = client.get("/api/v1/agents/get-test-agent")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "get-test-agent"


def test_get_agent_not_found(client):
    """Test getting a non-existent agent."""
    response = client.get("/api/v1/agents/non-existent-agent")
    assert response.status_code == 404


def test_delete_agent(client):
    """Test deleting an agent."""
    agent_definition = {
        "definition": {
            "name": "delete-test-agent",
            "display_name": "Delete Test Agent",
            "description": "An agent for delete test",
            "system_prompt": "You are a test agent.",
            "model": "gpt-4o",
            "tools": [],
            "sub_agents": [],
            "metadata": {},
        },
        "deploy_immediately": False,
    }

    client.post("/api/v1/agents", json=agent_definition)

    response = client.delete("/api/v1/agents/delete-test-agent")
    assert response.status_code == 204

    response = client.get("/api/v1/agents/delete-test-agent")
    assert response.status_code == 404
