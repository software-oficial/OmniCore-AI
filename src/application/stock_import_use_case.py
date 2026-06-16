import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.infrastructure.repositories.stock_repository import StockRepository

logger = logging.getLogger("OmniCore.StockImportUseCase")


class StockImportUseCase:
    """
    Application Layer: Orchestrates mass product imports and data mapping.
    """

    def __init__(self, session: Session):
        self.repo = StockRepository(session)

    def _auto_detect_mapping(self, raw_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Analyzes raw data headers and automatically detects the mapping based on common keywords.
        """
        if not raw_data:
            return {}

        headers = list(raw_data[0].keys())
        patterns = {
            "code": ["codigo", "code", "sku", "id", "barcode", "ean", "ref"],
            "name": [
                "nombre",
                "name",
                "producto",
                "item",
                "descripcion",
                "desc",
                "artículo",
            ],
            "price": ["precio", "price", "cost", "valor", "monto", "unit_price"],
            "quantity": [
                "cantidad",
                "qty",
                "quantity",
                "stock",
                "amount",
                "existencia",
            ],
            "category": ["categoria", "category", "tipo", "type", "grupo", "group"],
            "is_weight": ["peso", "weight", "kilo", "kg", "is_weight", "gramos"],
        }

        detected_mapping = {}
        for internal_field, keywords in patterns.items():
            for header in headers:
                header_lower = header.lower()
                if any(kw in header_lower for kw in keywords):
                    detected_mapping[internal_field] = header
                    break

        return detected_mapping

    def _map_row(self, row: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Translates a raw data row to internal fields with type cleaning."""
        mapped = {}
        for internal_field, source_col in mapping.items():
            val = row.get(source_col)

            if internal_field in ["price", "quantity"]:
                try:
                    if val is not None:
                        clean_val = str(val).replace("$", "").replace(",", "").strip()
                        val = float(clean_val)
                except (ValueError, TypeError):
                    val = 0.0

            if internal_field == "is_weight":
                if isinstance(val, str):
                    val = val.lower() in ["yes", "1", "true", "si"]
                elif isinstance(val, (int, float)):
                    val = bool(val)

            mapped[internal_field] = val
        return mapped

    def preview_import(
        self,
        raw_data: List[Dict[str, Any]],
        custom_mapping: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Previews the import by applying the mapping.
        Returns transformed data for user validation.
        """
        if not raw_data:
            return {"status": "error", "message": "No hay datos para procesar."}

        mapping = custom_mapping or self._auto_detect_mapping(raw_data)

        if not mapping:
            return {
                "status": "needs_mapping",
                "message": "Se requiere definir el mapeo de columnas manualmente.",
                "headers": list(raw_data[0].keys()),
                "sample_data": raw_data[:5],
            }

        preview_data = []
        for i, row in enumerate(raw_data, start=1):
            try:
                mapped_row = self._map_row(row, mapping)
                preview_data.append({"row": i, "original": row, "mapped": mapped_row})
            except Exception as e:
                preview_data.append({"row": i, "original": row, "error": str(e)})

        return {
            "status": "success",
            "data": preview_data,
            "count": len(preview_data),
            "mapping_used": mapping,
        }

    def execute_bulk_add(
        self, context: CoreContext, products: List[Dict[str, Any]]
    ) -> ServiceResponse:
        try:
            success_count = 0
            error_count = 0

            for p in products:
                try:
                    code = p.get("code")
                    name = p.get("name")
                    price = p.get("price")
                    quantity = p.get("cantidad", p.get("quantity", 0))
                    category = p.get("category")
                    is_weight = p.get("is_weight", False)

                    if not code or not name or price is None:
                        error_count += 1
                        continue

                    _ = self.repo.upsert_product(
                        code, name, price, quantity, category, is_weight
                    )
                    self.repo.record_movement(
                        code, quantity, "BULK_IMPORT", context.user_id
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(
                        f"Error processing product {p.get('code')} during bulk add: {e}"
                    )
                    error_count += 1

            return ServiceResponse.success_res(
                data={"success": success_count, "errors": error_count},
                message=f"Bulk processing completed. {success_count} added, {error_count} failed.",
            )
        except Exception as e:
            logger.error(f"Error in bulk_add_products: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "STOCK_BULK_ADD_ERROR"
            )

    def execute_validated_import(
        self, context: CoreContext, products: List[Dict[str, Any]]
    ) -> ServiceResponse:
        # Pre-validation
        for p in products:
            if not p.get("code") or not p.get("name") or p.get("price") is None:
                return ServiceResponse.error_res(
                    f"Validation failed for product {p.get('code', 'Unknown')}: Missing required fields.",
                    "IMPORT_VALIDATION_ERROR",
                )

        return self.execute_bulk_add(context, products)

    def execute_mapped_import(
        self, context: CoreContext, data: List[Dict[str, Any]], mapping: Dict[str, str]
    ) -> ServiceResponse:
        try:
            normalized_products = []
            for row in data:
                normalized = self._map_row(row, mapping)

                if (
                    not normalized["code"]
                    or not normalized["name"]
                    or normalized["price"] is None
                ):
                    return ServiceResponse.error_res(
                        f"Mapping error: Row missing required data. Row: {row}",
                        "MAPPING_VALIDATION_ERROR",
                    )
                normalized_products.append(normalized)

            return self.execute_bulk_add(context, normalized_products)
        except Exception as e:
            logger.error(f"Error in import_with_mapping: {e}")
            return ServiceResponse.error_res(
                f"Import failed: {str(e)}", "IMPORT_MAPPING_ERROR"
            )
