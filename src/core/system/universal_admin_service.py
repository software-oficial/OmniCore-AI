import json
import logging
import uuid
from typing import Any, Dict

from sqlalchemy import text

from src.core.auth.token_manager import token_manager
from src.core.dispatcher.core_types import ServiceResponse
from src.infrastructure.db.core_db_manager import core_db_manager

logger = logging.getLogger("OmniCore.UniversalAdminService")


class UniversalAdminService:
    """
    Universal Administration Service (UUS).
    Allows managing everything (Users, Businesses, Stock, Credentials) via URL.
    """

    def setup_business_and_owner(
        self, username: str, password_hash: str, business_name: str, plan: str = "FREE"
    ) -> ServiceResponse:
        """Creates a business and its primary owner in a single transaction."""
        user_id = str(uuid.uuid4())
        business_id = str(uuid.uuid4())

        try:
            with core_db_manager.get_session() as session:
                # 1. Create Business
                session.execute(
                    text(
                        "INSERT INTO businesses (id, name, owner_id, plan) VALUES (:bid, :name, :uid, :plan)"
                    ),
                    {
                        "bid": business_id,
                        "name": business_name,
                        "uid": user_id,
                        "plan": plan,
                    },
                )

                # 2. Create User
                session.execute(
                    text(
                        "INSERT INTO users (id, username, password_hash, business_id, role) VALUES (:uid, :user, :pass, :bid, 'OWNER')"
                    ),
                    {
                        "uid": user_id,
                        "user": username,
                        "pass": password_hash,
                        "bid": business_id,
                    },
                )

                # 3. Assign Default Infrastructure (Crucial for DB Pool initialization)
                try:
                    session.execute(
                        text(
                            """
                            INSERT INTO app_infrastructure (app_id, db_host, db_port, db_user, db_password, db_name, tier)
                            VALUES (:app_id, :host, :port, :user, :pass, :dbname, :tier)
                            """
                        ),
                        {
                            "app_id": business_id,
                            "host": "nozomi.proxy.rlwy.net",
                            "port": 34662,
                            "user": "postgres",
                            "pass": "FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW",
                            "dbname": "railway",
                            "tier": plan,
                        },
                    )
                except Exception as infra_e:
                    logger.warning(
                        f"Could not set default infra for {business_id}: {infra_e}"
                    )

                # 4. Initialize Cash Box (Crucial for Sales Flow)
                try:
                    session.execute(
                        text(
                            "INSERT INTO cash_box (app_id, abierta, efectivo_inicial) VALUES (:app_id, false, 0)"
                        ),
                        {"app_id": business_id},
                    )
                except Exception as cash_e:
                    logger.error(
                        f"Could not initialize cash box for {business_id}: {cash_e}"
                    )

                # Generate a long-lived token for immediate use
                token = token_manager.generate_token(
                    agent_id=user_id,
                    app_id=business_id,
                    dev_id="SYSTEM",
                    user_id=user_id,
                    tier=plan,
                    permissions=["MASTER"],
                )

                return ServiceResponse.success_res(
                    data={
                        "user_id": user_id,
                        "business_id": business_id,
                        "token": token,
                    },
                    message=f"Business '{business_name}' and owner '{username}' created successfully.",
                )
        except Exception as e:
            logger.error(f"Setup error: {e}")
            return ServiceResponse.error_res(f"Setup failed: {str(e)}", "SETUP_ERROR")

    def add_employee(
        self,
        business_id: str,
        username: str,
        password_hash: str,
        role: str = "EMPLOYEE",
    ) -> ServiceResponse:
        """Adds an employee to an existing business."""
        user_id = str(uuid.uuid4())
        try:
            core_db_manager.execute_raw(
                text(
                    "INSERT INTO users (id, username, password_hash, business_id, role) VALUES (:uid, :user, :pass, :bid, :role)"
                ),
                {
                    "uid": user_id,
                    "user": username,
                    "pass": password_hash,
                    "bid": business_id,
                    "role": role,
                },
            )
            return ServiceResponse.success_res(
                data={"user_id": user_id},
                message=f"Employee '{username}' added to business {business_id}.",
            )
        except Exception as e:
            logger.error(f"Error adding employee: {e}")
            return ServiceResponse.error_res(f"Failed to add employee: {str(e)}")

    def set_credentials(
        self, business_id: str, provider: str, data: Dict[str, Any]
    ) -> ServiceResponse:
        """Sets or updates external API credentials for a business."""
        try:
            json_data = json.dumps(data)
            # Upsert logic
            existing = core_db_manager.execute_raw(
                text(
                    "SELECT id FROM credentials WHERE business_id = :bid AND provider = :provider"
                ),
                {"bid": business_id, "provider": provider},
            ).fetchone()

            if existing:
                core_db_manager.execute_raw(
                    text("UPDATE credentials SET data = :data WHERE id = :id"),
                    {"data": json_data, "id": existing[0]},
                )
            else:
                core_db_manager.execute_raw(
                    text(
                        "INSERT INTO credentials (business_id, provider, data) VALUES (:bid, :provider, :data)"
                    ),
                    {"bid": business_id, "provider": provider, "data": json_data},
                )

            return ServiceResponse.success_res(
                message=f"Credentials for {provider} updated."
            )
        except Exception as e:
            return ServiceResponse.error_res(f"Failed to set credentials: {str(e)}")

    def sync_stock(
        self, business_id: str, sku: str, data: Dict[str, Any]
    ) -> ServiceResponse:
        """Upserts a stock item with flexible JSON data."""
        try:
            json_data = json.dumps(data)
            core_db_manager.execute_raw(
                text(
                    """
                INSERT INTO stock (business_id, sku, data) VALUES (:bid, :sku, :data)
                ON CONFLICT(business_id, sku) DO UPDATE SET data = excluded.data, updated_at = CURRENT_TIMESTAMP
                """
                ),
                {"bid": business_id, "sku": sku, "data": json_data},
            )
            return ServiceResponse.success_res(message=f"Stock item {sku} synced.")
        except Exception as e:
            return ServiceResponse.error_res(f"Stock sync failed: {str(e)}")


universal_admin_service = UniversalAdminService()
