import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command
from src.domains.stock.stock_service import stock_service

logger = logging.getLogger("OmniCore.SystemService")


class SystemService:
    """
    Pure Business Logic for System Administration and Preferences.
    Manages tenant-specific settings and data exports.
    Stateless and depends on injected session.
    """

    @command(
        name="sys.set_setting",
        description="Saves a specific configuration setting for the business (e.g., theme, language, bot_welcome_msg).",
        params_model={"key": "string", "value": "string"},
    )
    def set_setting(
        self, session: Session, context: CoreContext, key: str, value: str
    ) -> ServiceResponse:
        """
        Persists a setting in the client's external database.
        """
        try:
            query = text(
                """
                INSERT INTO settings (key, value) VALUES (:key, :value)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """
            )
            session.execute(query, {"key": key, "value": value})

            return ServiceResponse.success_res(
                message=f"Setting '{key}' has been updated successfully."
            )
        except Exception as e:
            logger.error(f"Error setting system preference {key}: {e}")
            return ServiceResponse.error_res(
                f"Failed to save setting: {str(e)}", "SETTING_SAVE_ERROR"
            )

    @command(
        name="sys.get_setting",
        description="Retrieves a specific configuration setting for the business.",
        params_model={"key": "string"},
    )
    def get_setting(
        self, session: Session, context: CoreContext, key: str
    ) -> ServiceResponse:
        """
        Retrieves a setting from the client's external database.
        """
        try:
            query = text("SELECT value FROM settings WHERE key = :key")
            result = session.execute(query, {"key": key}).mappings().first()

            if result:
                return ServiceResponse.success_res(
                    data={"value": result["value"]},
                    message=f"Setting '{key}' retrieved.",
                )

            return ServiceResponse.success_res(
                data=None, message=f"Setting '{key}' not found."
            )
        except Exception as e:
            logger.error(f"Error retrieving setting {key}: {e}")
            return ServiceResponse.error_res(
                f"Failed to retrieve setting: {str(e)}", "SETTING_GET_ERROR"
            )

    @command(
        name="sys.export_inventory",
        description="Generates the inventory data in CSV format for export.",
        params_model={},
    )
    def export_inventory(
        self, session: Session, context: CoreContext
    ) -> ServiceResponse:
        """
        Retrieves inventory data and returns it in a format suitable for CSV export.
        Does NOT save files to the server to remain stateless.
        """
        try:
            # Reuse the stock_service to get the product list
            # This ensures we use the same filters and logic as the list command
            res = stock_service.list_products(session=session, context=context)

            if not res.success or not res.data:
                return ServiceResponse.error_res(
                    "No products available for export.", "EXPORT_NO_DATA"
                )

            # Build CSV content in memory
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Headers
            writer.writerow(
                ["Código", "Nombre", "Precio", "Cantidad", "Categoría", "Es Peso"]
            )

            for p in res.data:
                writer.writerow(
                    [
                        p.get("codigo"),
                        p.get("nombre"),
                        p.get("precio"),
                        p.get("cantidad"),
                        p.get("categoria"),
                        "SÍ" if p.get("es_peso") else "NO",
                    ]
                )

            return ServiceResponse.success_res(
                data={"csv_content": output.getvalue()},
                message="Inventory data generated for CSV export.",
            )
        except Exception as e:
            logger.error(f"Export error: {e}")
            return ServiceResponse.error_res(f"Export failed: {str(e)}", "EXPORT_ERROR")


# Singleton for the dispatcher
system_service = SystemService()
