import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.application.stock_import_use_case import StockImportUseCase
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command

logger = logging.getLogger("OmniCore.StockImportService")


class StockImportService:
    """
    Domain Layer: Exposes mass stock import capabilities as executable commands.
    Allows the owner to upload product lists via CSV/Excel and map them to internal fields.
    """

    @command(
        name="stock.import.preview",
        description="Previews a stock import by automatically detecting column mapping.",
        params_model={"raw_data": "list", "custom_mapping": "dict"},
    )
    def preview_import(
        self,
        session: Session,
        context: CoreContext,
        raw_data: List[Dict[str, Any]],
        custom_mapping: Optional[Dict[str, str]] = None,
    ) -> ServiceResponse:
        """
        Processes raw data and returns a preview of how it will be mapped.
        """
        try:
            use_case = StockImportUseCase(session)
            preview = use_case.preview_import(raw_data, custom_mapping)

            if preview.get("status") == "error":
                return ServiceResponse.error_res(
                    preview["message"], "IMPORT_PREVIEW_ERROR"
                )

            return ServiceResponse.success_res(
                data=preview, message="Import preview generated successfully."
            )
        except Exception as e:
            logger.error(f"Error in preview_import command: {e}")
            return ServiceResponse.error_res(
                f"Internal error during preview: {str(e)}", "IMPORT_PREVIEW_ERROR"
            )

    @command(
        name="stock.import.execute",
        description="Executes the bulk import of products using a validated mapping.",
        params_model={"raw_data": "list", "mapping": "dict"},
    )
    def execute_import(
        self,
        session: Session,
        context: CoreContext,
        raw_data: List[Dict[str, Any]],
        mapping: Dict[str, str],
    ) -> ServiceResponse:
        """
        Applies the mapping and performs the bulk upsert of products into the DB.
        """
        try:
            use_case = StockImportUseCase(session)
            return use_case.execute_mapped_import(context, raw_data, mapping)
        except Exception as e:
            logger.error(f"Error in execute_import command: {e}")
            return ServiceResponse.error_res(
                f"Internal error during execution: {str(e)}", "IMPORT_EXEC_ERROR"
            )


# Singleton
stock_import_service = StockImportService()
