import os

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

# Mock Master Key
os.environ["OMNICORE_MASTER_KEY"] = "test-master-key"


def test_dev_onboard_client_success():
    """Test onboarding a new client with strict typing."""
    payload = {
        "agent_id": "agent_123",
        "app_name": "Supermarket Alpha",
        "db_config": {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "password",
            "dbname": "alpha_db",
        },
        "tier": "GOLD",
    }
    headers = {"Authorization": "test-master-key"}
    response = client.post("/api/dev/clients/onboard", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "app_id" in data


def test_dev_onboard_client_invalid_type():
    """Test that invalid types trigger 422 Unprocessable Entity (Pydantic validation)."""
    payload = {
        "agent_id": "agent_123",
        "app_name": "Supermarket Alpha",
        "db_config": {
            "host": "localhost",
            "port": "not-a-number",  # Invalid type
            "user": "postgres",
            "password": "password",
            "dbname": "alpha_db",
        },
    }
    headers = {"Authorization": "test-master-key"}
    response = client.post("/api/dev/clients/onboard", json=payload, headers=headers)
    assert response.status_code == 422  # Pydantic validation error


def test_dev_forbidden_access():
    """Test that requests without the master key are forbidden."""
    payload = {
        "agent_id": "agent_123",
        "app_name": "Supermarket Alpha",
        "db_config": {
            "host": "l",
            "port": 5432,
            "user": "u",
            "password": "p",
            "dbname": "d",
        },
    }
    headers = {"Authorization": "wrong-key"}
    response = client.post("/api/dev/clients/onboard", json=payload, headers=headers)
    assert response.status_code == 403


def test_dev_create_plan_success():
    """Test creating a subscription plan."""
    payload = {"tier_name": "Plan Diamante", "level": 10}
    headers = {"Authorization": "test-master-key"}
    response = client.post("/api/dev/plans", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_dev_map_command_plan_success():
    """Test mapping a command to a plan."""
    payload = {"command_name": "sales.report.advanced", "min_tier": "PLAN_DIAMANTE"}
    headers = {"Authorization": "test-master-key"}
    response = client.post("/api/dev/plans/commands", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
