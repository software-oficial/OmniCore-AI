import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.application.inventory_management_use_case import InventoryManagementUseCase
from src.application.stock_audit_use_case import StockAuditUseCase
from src.application.stock_import_use_case import StockImportUseCase
from src.application.stock_sync_use_case import StockSyncUseCase
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command

logger = logging.getLogger("OmniCore.StockService")


class ProductImportItem(BaseModel):
    """Strict model for a product import item."""

    code: str = Field(..., description="Unique SKU/code of the variant")
    name: str = Field(..., description="Name of the product")
    price: float = Field(..., gt=0, description="Unit price must be positive")
    quantity: int = Field(..., ge=0, description="Initial quantity")
    category: Optional[str] = Field(None, description="Product category")
    is_weight: bool = Field(False, description="Whether the product is sold by weight")


class StockImportModel(BaseModel):
    """Strict contract for stock import commands."""

    products: List[ProductImportItem] = Field(
        ..., min_length=1, description="List of products to import"
    )


class StockAuditItem(BaseModel):
    """Strict model for an audit entry."""

    code: str = Field(..., description="Unique SKU/code of the variant")
    physical_count: int = Field(
        ..., ge=0, description="Actual count found during audit"
    )


class StockAuditModel(BaseModel):
    """Strict contract for the inventory audit command."""

    audit_data: List[StockAuditItem] = Field(
        ..., min_length=1, description="List of audited products"
    )


class StockService:
    """
    Professional Stock Management Service.
    Handles the relation between Products and Variants with a full Ledger audit trail.
    """

    @command(
        name="stock.sync_delta",
        description="Retrieves variants that have changed since a timestamp. Optimized for sync.",
        params_model={"since": "string"},
    )
    def get_sync_delta(
        self, session: Session, context: CoreContext, since: str
    ) -> ServiceResponse:
        return StockSyncUseCase(session).execute_get_delta(context, since)

    @command(
        name="stock.import_validated",
        description="Imports products and variants with pre-validation.",
        params_model=StockImportModel,
    )
    def import_validated(
        self, session: Session, context: CoreContext, products: List[Dict[str, Any]]
    ) -> ServiceResponse:
        return StockImportUseCase(session).execute_validated_import(context, products)

    @command(
        name="stock.add",
        description="Adds a product and its primary variant. Upserts if SKU exists.",
        params_model={
            "code": "string",
            "name": "string",
            "price": "float",
            "quantity": "int",
            "category": "string",
            "is_weight": "boolean",
        },
    )
    def add_product(
        self,
        session: Session,
        context: CoreContext,
        code: str,
        name: str,
        price: float,
        quantity: int,
        category: Optional[str] = None,
        is_weight: bool = False,
    ) -> ServiceResponse:
        return InventoryManagementUseCase(session, context.app_id).execute_add_product(
            context, code, name, price, quantity, category, is_weight
        )

    @command(
        name="stock.get",
        description="Retrieves a variant and its parent product data.",
        params_model={"code": "string"},
    )
    def get_product(
        self, session: Session, context: CoreContext, code: str
    ) -> ServiceResponse:
        return InventoryManagementUseCase(session, context.app_id).execute_get_product(
            code
        )

    @command(
        name="stock.update",
        description="Updates variant quantity and records the movement in the ledger.",
        params_model={"code": "string", "quantity": "int", "reason": "string"},
    )
    def update_stock(
        self,
        session: Session,
        context: CoreContext,
        code: str,
        quantity: int,
        reason: str = "MANUAL",
    ) -> ServiceResponse:
        return InventoryManagementUseCase(session, context.app_id).execute_update_stock(
            context, code, quantity, reason
        )

    @command(
        name="stock.list",
        description="Lists variants, optionally filtered by parent category.",
        params_model={"category": "string", "filter_text": "string"},
    )
    def list_products(
        self,
        session: Session,
        context: CoreContext,
        category: Optional[str] = None,
        filter_text: Optional[str] = None,
    ) -> ServiceResponse:
        return InventoryManagementUseCase(
            session, context.app_id
        ).execute_list_products(category, filter_text)

    @command(
        name="stock.history",
        description="Retrieves the full ledger history for a specific SKU.",
        params_model={"code": "string"},
    )
    def get_stock_history(
        self, session: Session, context: CoreContext, code: str
    ) -> ServiceResponse:
        return InventoryManagementUseCase(session, context.app_id).execute_get_history(
            code
        )

    @command(
        name="stock.low",
        description="Lists variants below their specific min_threshold.",
        params_model={"threshold": "float"},
    )
    def get_low_stock(
        self, session: Session, context: CoreContext, threshold: float = 5.0
    ) -> ServiceResponse:
        return InventoryManagementUseCase(
            session, context.app_id
        ).execute_get_low_stock(threshold)

    @command(
        name="stock.delete",
        description="Deletes a variant and its stock records.",
        params_model={"code": "string"},
    )
    def delete_product(
        self, session: Session, context: CoreContext, code: str
    ) -> ServiceResponse:
        return InventoryManagementUseCase(
            session, context.app_id
        ).execute_delete_product(code)

    @command(
        name="stock.bulk_add",
        description="Adds multiple variants in a single transaction.",
        params_model=StockImportModel,
    )
    def bulk_add_products(
        self, session: Session, context: CoreContext, products: List[Dict[str, Any]]
    ) -> ServiceResponse:
        return StockImportUseCase(session).execute_bulk_add(context, products)

    @command(
        name="stock.audit_inventory",
        description="Performs a full audit and records discrepancies in the ledger.",
        params_model=StockAuditModel,
    )
    def audit_inventory(
        self, session: Session, context: CoreContext, audit_data: List[Dict[str, Any]]
    ) -> ServiceResponse:
        return StockAuditUseCase(session).execute_audit(context, audit_data)

    @command(
        name="stock.transfer",
        description="Transfers stock between zones, recording ledger movements.",
        params_model={
            "code": "string",
            "amount": "int",
            "from_zone": "string",
            "to_zone": "string",
        },
    )
    def transfer_stock(
        self,
        session: Session,
        context: CoreContext,
        code: str,
        amount: int,
        from_zone: str,
        to_zone: str,
    ) -> ServiceResponse:
        return InventoryManagementUseCase(session, context.app_id).execute_transfer(
            context, code, amount, from_zone, to_zone
        )


stock_service = StockService()
