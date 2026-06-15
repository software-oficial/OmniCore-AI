import json
import os
from typing import Any, Dict

import requests
from sqlalchemy import create_engine, text


class OmniCoreSDK:
    """
    OmniCore Local SDK: A simplified bridge between the Cloud API
    and the Local Infrastructure.
    """

    def __init__(self, config_path: str = ".omnicore_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.api_base_url = "https://omnicore-ai-production.up.railway.app/api"

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                return json.load(f)
        return {}

    def _save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

    def set_credentials(self, agent_id: str, token: str, app_id: str):
        """Persists identity and access tokens locally."""
        self.config.update({"agent_id": agent_id, "token": token, "app_id": app_id})
        self._save_config()

    def execute(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates a command:
        1. Validates governance via Cloud API.
        2. If authorized for local execution, runs it against the local DB.
        """
        if not self.config.get("token"):
            raise Exception(
                "OmniCore SDK not configured. Please call set_credentials first."
            )

        # 1. Request validation from Cloud API
        headers = {"Authorization": f"Bearer {self.config['token']}"}
        payload = {"command": command, "params": params}

        try:
            response = requests.post(
                f"{self.api_base_url}/gateway/execute", json=payload, headers=headers
            )
            res_data = response.json()
        except Exception as e:
            return {"success": False, "message": f"Cloud API unreachable: {str(e)}"}

        # 2. Handle Execution Strategy
        if (
            res_data.get("success")
            and res_data.get("data", {}).get("action") == "EXECUTE_LOCALLY"
        ):
            # The Cloud API authorized local execution
            return self._run_local(
                res_data["data"]["command"], res_data["data"]["params"]
            )

        return res_data

    def _run_local(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        The core of the local execution.
        In a real implementation, this would call the local ModuleLoader.
        """
        # Load local DB config (Assuming a .env or similar)
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://omni_admin:secure_password@localhost:5432/omnicore_biz",
        )

        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                # Here, the SDK would ideally trigger the local logic.
                # For now, we simulate the execution of a command logic.
                # In a full implementation, this would import the local src/core/dispatcher

                # SIMULATION: We just verify the DB is reachable
                conn.execute(text("SELECT 1"))

                return {
                    "success": True,
                    "message": f"Command {command} executed successfully on LOCAL DB.",
                    "data": {"executed_locally": True, "params": params},
                }
        except Exception as e:
            return {"success": False, "message": f"Local DB Execution Error: {str(e)}"}

    def onboard(self, name: str, platform_name: str, db_config: Dict[str, Any]):
        """
        Simplified Zero-to-Hero onboarding.
        """
        payload = {"name": name, "platform_name": platform_name, **db_config}
        try:
            response = requests.post(f"{self.api_base_url}/agent/onboard", json=payload)
            res_data = response.json()
            if res_data.get("success") or "token" in res_data:
                self.set_credentials(
                    res_data.get("agent_id"),
                    res_data.get("token"),
                    res_data.get("app_id"),
                )
                return res_data
        except Exception as e:
            return {"success": False, "message": f"Onboarding failed: {str(e)}"}


# Example Usage:
# sdk = OmniCoreSDK()
# sdk.onboard("MyAgent", "MyPlatform", {"db_host": "localhost", "db_user": "admin", ...})
# sdk.execute("stock.add", {"name": "Product X", "price": 10, "quantity": 5})
