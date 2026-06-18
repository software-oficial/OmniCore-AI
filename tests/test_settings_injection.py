import asyncio
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.application.command_dispatcher import command_dispatcher
from src.core.module_loader import module_loader
from src.infrastructure.db.db_manager import db_manager

# --- Configuration ---
TEST_DB_URL = "sqlite:///test_omnicore_settings.db"
engine = create_engine(TEST_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    with SessionLocal() as session:
        # Business Table for Settings
        session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS business_settings (
                    setting_key VARCHAR(100) PRIMARY KEY,
                    setting_value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
        )
        session.commit()


@pytest.mark.asyncio
async def test_settings_injection():
    """
    Test that business settings are correctly injected into CoreContext
    and available to the handler.
    """
    # 1. Seed a setting in the business DB
    with SessionLocal() as session:
        session.execute(
            text(
                "INSERT OR REPLACE INTO business_settings (setting_key, setting_value, description) VALUES (:k, :v, :d)"
            ),
            {"k": "store_name", "v": "OmniStore Test", "d": "Nombre de la tienda"},
        )
        session.commit()

    # 2. Create a mock handler that returns the injected settings
    async def mock_handler(session, context, **params):
        return {"store_name": context.settings.get("store_name")}

    # Register the mock handler
    module_loader._command_registry["test.settings"] = {
        "handler": mock_handler,
        "description": "Test handler",
        "params_model": None,
        "is_system": False,
    }

    # 3. Setup Mocks for the Dispatcher Pipeline
    # Mock token validation
    with patch(
        "src.core.auth.token_manager.token_manager.validate_token"
    ) as mock_token:
        mock_token.return_value = (True, {"agent_id": "test_agent"}, "FREE")

        # Mock infrastructure lookup
        with patch(
            "src.core.registry.infrastructure_registry.infrastructure_registry.get_app_context"
        ) as mock_infra:
            mock_infra.return_value = {
                "app_id": "test_app",
                "db_config": {"url": TEST_DB_URL},
                "tier": "FREE",
            }

            # Mock Governance to allow the command
            with patch(
                "src.core.governance.governance_service.governance_service.validate_access"
            ) as mock_gov:
                mock_gov.return_value = (True, None)

                # Mock db_manager.get_session to return a real session in an async context manager
                class AsyncSessionMock:
                    async def __aenter__(self):
                        return SessionLocal()

                    async def __aexit__(self, exc_type, exc_val, exc_tb):
                        pass

                with patch.object(
                    db_manager, "get_session", return_value=AsyncSessionMock()
                ):
                    # Execute the command
                    result = await command_dispatcher.dispatch(
                        "test.settings",
                        "test-token",
                        {},
                        ctx_override=None,  # Let it build the context naturally
                    )

                    # 4. Validation
                    assert result.success is True
                    assert result.data["store_name"] == "OmniStore Test"


if __name__ == "__main__":
    # To run this manually without pytest-asyncio
    asyncio.run(test_settings_injection())
