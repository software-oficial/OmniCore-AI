import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.application.stock_import_use_case import StockImportUseCase
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command

logger = logging.getLogger("OmniCore.ImportService")


class ImportService:
    """
    Thin Delegate for Inventory Import.
    Handles the interaction between raw data formats and the Import Use Case.
    """

    def __init__(self):
        self.logger = logging.getLogger("ImportService")

    def preview_import(
        self,
        session: Session,
        context: CoreContext,
        raw_data: List[Dict[str, Any]],
        custom_mapping: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Previsualiza la importación aplicando el mapeo.
        Devuelve los datos transformados para que el usuario los valide antes del commit.
        """
        # Note: The mapping logic is now handled by the Use Case for architectural consistency
        use_case = StockImportUseCase(session)
        return use_case.preview_import(raw_data, custom_mapping)

    @command(
        name="stock.import.commit",
        description="Commits a previously previewed import to the inventory.",
        params_model={"import_id": "string"},
    )
    def commit_import(
        self, session: Session, context: CoreContext, data_list: List[Dict[str, Any]]
    ) -> ServiceResponse:
        """
        Inserta la lista de productos validados en el inventario del tenant.
        """
        # The logic of iterating and calling add_product is now in StockImportUseCase.execute_bulk_add
        # We extract the 'mapped' data from the preview result list
        mapped_products = [item.get("mapped", {}) for item in data_list]
        return StockImportUseCase(session).execute_bulk_add(context, mapped_products)


# Singleton para acceso global
import_service = ImportService()
