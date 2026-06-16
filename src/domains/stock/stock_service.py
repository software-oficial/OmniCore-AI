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

    code: str = Field(..., description="Unique SKU/code of the product")
    name: str = Field(..., description="Full name of the product")
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

    code: str = Field(..., description="Unique SKU/code of the product")
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
    Thin Delegate for Stock Management.
    Orchestrates the execution of Use Cases.
    """

    @command(
        name="stock.sync_delta",
        description="Retrieves only the products that have changed since a given timestamp. Optimized for mobile app synchronization.",
        params_model={"since": "string"},
    )
    def get_sync_delta(
        self, session: Session, context: CoreContext, since: str
    ) -> ServiceResponse:
        return StockSyncUseCase(session).execute_get_delta(since)

    @command(
        name="stock.import_validated",
        description="Imports products from a list, performing a pre-validation check to avoid partial corruption.",
        params_model=StockImportModel,
    )
    def import_validated(
        self, session: Session, context: CoreContext, products: List[Dict[str, Any]]
    ) -> ServiceResponse:
        return StockImportUseCase(session).execute_validated_import(context, products)

    @command(
        name="stock.import_with_mapping",
        description="Imports products using a dynamic mapping definition. Translates user-defined column names to internal fields.",
        params_model={"data": "list[dict]", "mapping": "dict"},
    )
    def import_with_mapping(
        self,
        session: Session,
        context: CoreContext,
        data: List[Dict[str, Any]],
        mapping: Dict[str, str],
    ) -> ServiceResponse:
        return StockImportUseCase(session).execute_mapped_import(context, data, mapping)

    @command(
        name="stock.add",
        description="Adds a new product and records the initial movement in the ledger. Upserts if code exists.",
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
        return InventoryManagementUseCase(session).execute_add_product(
            context, code, name, price, quantity, category, is_weight
        )

    @command(
        name="stock.get",
        description="Retrieves a single product by its unique code.",
        params_model={"code": "string"},
    )
    def get_product(
        self, session: Session, context: CoreContext, code: str
    ) -> ServiceResponse:
        return InventoryManagementUseCase(session).execute_get_product(code)

    @command(
        name="stock.update",
        description="Updates the quantity of a product using atomic transactions. Prevents negative stock.",
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
        return InventoryManagementUseCase(session).execute_update_stock(
            context, code, quantity, reason
        )

    @command(
        name="stock.list",
        description="Lists products, optionally filtered by category or text search.",
        params_model={"category": "string", "filter_text": "string"},
    )
    def list_products(
        self,
        session: Session,
        context: CoreContext,
        category: Optional[str] = None,
        filter_text: Optional[str] = None,
    ) -> ServiceResponse:
        return InventoryManagementUseCase(session).execute_list_products(
            category, filter_text
        )

    @command(
        name="stock.history",
        description="Retrieves the movement history for a specific product.",
        params_model={"code": "string"},
    )
    def get_stock_history(
        self, session: Session, context: CoreContext, code: str
    ) -> ServiceResponse:
        return InventoryManagementUseCase(session).execute_get_history(code)

    @command(
        name="stock.low",
        description="Lists products that are below the critical threshold.",
        params_model={"threshold": "float"},
    )
    def get_low_stock(
        self, session: Session, context: CoreContext, threshold: float = 5.0
    ) -> ServiceResponse:
        return InventoryManagementUseCase(session).execute_get_low_stock(threshold)

    @command(
        name="stock.delete",
        description="Deletes a product from the inventory.",
        params_model={"code": "string"},
    )
    def delete_product(
        self, session: Session, context: CoreContext, code: str
    ) -> ServiceResponse:
        return InventoryManagementUseCase(session).execute_delete_product(code)

    @command(
        name="stock.bulk_add",
        description="Adds multiple products in a single transaction. Optimized for large imports.",
        params_model=StockImportModel,
    )
    def bulk_add_products(
        self, session: Session, context: CoreContext, products: List[Dict[str, Any]]
    ) -> ServiceResponse:
        return StockImportUseCase(session).execute_bulk_add(context, products)

    @command(
        name="stock.audit_inventory",
        description="Performs a full inventory audit by comparing recorded stock with a physical count. Records discrepancies in the ledger.",
        params_model=StockAuditModel,
    )
    def audit_inventory(
        self, session: Session, context: CoreContext, audit_data: List[Dict[str, Any]]
    ) -> ServiceResponse:
        return StockAuditUseCase(session).execute_audit(context, audit_data)

    @command(
        name="stock.transfer",
        description="Transfers stock between different warehouse locations or zones.",
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
        return InventoryManagementUseCase(session).execute_transfer(
            context, code, amount, from_zone, to_zone
        )


stock_service = StockService()
