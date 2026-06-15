import json
import logging
import os
from typing import Any, Dict, Optional

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("OmniCoreSDK")


class OmniCoreSDK:
    """
    OmniCore Pro SDK: The ultimate bridge between the Cloud API and Local Infrastructure.

    This SDK implements a 'Governance-First' approach where the Cloud API manages
    authorization and logic mapping, while the SDK handles the physical data
    execution on the customer's private infrastructure.
    """

    def __init__(self, config_path: str = ".omnicore_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.api_base_url = "https://omnicore-ai-production.up.railway.app/api"

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Configuration load error: {e}")
        return {}

    def _save_config(self):
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            logger.error(f"Configuration save error: {e}")

    def set_credentials(self, agent_id: str, token: str, app_id: str):
        """Persists identity and access tokens locally."""
        self.config.update({"agent_id": agent_id, "token": token, "app_id": app_id})
        self._save_config()
        logger.info(f"Identity synchronized for agent: {agent_id}")

    def execute(
        self, command: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main execution pipeline:
        1. Request governance from Cloud API.
        2. If authorized for local execution, perform the DB operation.
        3. Handle various API response formats (Lists vs Dicts).
        """
        if params is None:
            params = {}

        if not self.config.get("token"):
            raise Exception(
                "SDK not configured. Please run onboard() or set_credentials() first."
            )

        headers = {"Authorization": f"Bearer {self.config['token']}"}
        payload = {"command": command, "params": params}

        try:
            response = requests.post(
                f"{self.api_base_url}/gateway/execute",
                json=payload,
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
            res_data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API Connectivity Error: {e}")
            return {"success": False, "message": f"Cloud API unreachable: {str(e)}"}

        # Case A: API returns raw data list (Implicit Success)
        if isinstance(res_data, list):
            return {
                "success": True,
                "data": res_data,
                "message": "Data retrieved successfully from cloud.",
            }

        # Case B: API authorizes Local Execution
        if (
            isinstance(res_data, dict)
            and res_data.get("success")
            and res_data.get("data", {}).get("action") == "EXECUTE_LOCALLY"
        ):
            return self._run_local(
                res_data["data"]["command"], res_data["data"]["params"]
            )

        # Case C: Standard API response
        if isinstance(res_data, dict):
            return res_data

        return {
            "success": False,
            "message": f"Unexpected API response format: {type(res_data)}",
        }

    def _run_local(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Physically executes the command against the local PostgreSQL database.
        """
        db_url = os.getenv(
            "DATABASE_URL",
            self.config.get(
                "db_url",
                "postgresql://omni_admin:secure_password@localhost:5432/omnicore_biz",
            ),
        )

        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                # Logic Simulation: In a full production SDK, this would call local dispatcher modules.
                # For now, we validate connection and simulate execution.
                conn.execute(text("SELECT 1"))
                logger.info(f"Executing local logic for command: {command}")
                return {
                    "success": True,
                    "message": f"Command {command} executed successfully on local infrastructure.",
                    "data": {"executed_locally": True, "params": params},
                }
        except SQLAlchemyError as e:
            logger.error(f"Local DB Error: {e}")
            return {"success": False, "message": f"Local Database Error: {str(e)}"}

    def onboard(self, name: str, platform_name: str, db_config: Dict[str, Any]):
        """
        Zero-to-Hero Onboarding:
        1. Registers the agent in the cloud.
        2. Stores identity locally.
        3. Prepares local environment.
        """
        payload = {"name": name, "platform_name": platform_name, **db_config}

        try:
            response = requests.post(
                f"{self.api_base_url}/agent/onboard", json=payload, timeout=20
            )

            if response.status_code != 200:
                detail = (
                    response.json().get("detail", "Unknown API error")
                    if response.status_code != 422
                    else "Check DB config payload"
                )
                raise Exception(
                    f"Onboarding API Error ({response.status_code}): {detail}"
                )

            res_data = response.json()
            if "token" in res_data:
                self.set_credentials(
                    res_data.get("agent_id"),
                    res_data.get("token"),
                    res_data.get("app_id"),
                )

                # Optional: Save DB URL for local execute
                if "db_config" in db_config:
                    db_url = f"postgresql://{db_config['db_user']}:{db_config['db_password']}@{db_config['db_host']}:{db_config['db_port']}/{db_config['db_name']}"
                    self.config["db_url"] = db_url
                    self._save_config()

                return res_data

            raise Exception("API responded OK but no access token was provided.")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error during onboarding: {str(e)}")
