import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.dispatcher.core_types import CoreContext, ServiceResponse
from .stock_service import stock_service

logger = logging.getLogger("OmniCore.ImportService")

class ImportService:
    """
    Lógica de importación universal de inventario con mapeo dinámico de columnas.
    Permite migrar datos desde diversos formatos (CSV, Excel, JSON) sin configuración previa.
    """
    def __init__(self):
        self.logger = logging.getLogger("ImportService")

    def _auto_detect_mapping(self, raw_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Analiza las cabeceras de los datos crudos y detecta automáticamente 
        el mapeo basándose en patrones de palabras clave comunes.
        """
        if not raw_data:
            return {}

        headers = list(raw_data[0].keys())
        patterns = {
            'codigo': ['codigo', 'code', 'sku', 'id', 'barcode', 'ean', 'ref'],
            'nombre': ['nombre', 'name', 'producto', 'item', 'descripcion', 'desc', 'artículo'],
            'precio': ['precio', 'price', 'cost', 'valor', 'monto', 'unit_price'],
            'cantidad': ['cantidad', 'qty', 'quantity', 'stock', 'amount', 'existencia'],
            'categoria': ['categoria', 'category', 'tipo', 'type', 'grupo', 'group'],
            'es_peso': ['peso', 'weight', 'kilo', 'kg', 'is_weight', 'gramos']
        }

        detected_mapping = {}
        for internal_field, keywords in patterns.items():
            for header in headers:
                header_lower = header.lower()
                if any(kw in header_lower for kw in keywords):
                    detected_mapping[internal_field] = header
                    break
        
        self.logger.info(f"Auto-detección de mapeo completada: {detected_mapping}")
        return detected_mapping

    def preview_import(self, session: Session, context: CoreContext, raw_data: List[Dict[str, Any]], custom_mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Previsualiza la importación aplicando el mapeo.
        Devuelve los datos transformados para que el usuario los valide antes del commit.
        """
        if not raw_data:
            return {"status": "error", "message": "No hay datos para procesar."}
        
        mapping = custom_mapping or self._auto_detect_mapping(raw_data)
        
        if not mapping:
            return {
                "status": "needs_mapping", 
                "message": "Se requiere definir el mapeo de columnas manualmente.",
                "headers": list(raw_data[0].keys()),
                "sample_data": raw_data[:5]
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
            "mapping_used": mapping
        }

    def _map_row(self, row: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Traduce una fila de datos crudos a los campos internos del sistema con limpieza de tipos."""
        mapped = {}
        for internal_field, source_col in mapping.items():
            val = row.get(source_col)
            
            if internal_field in ['precio', 'cantidad']:
                try:
                    if val is not None:
                        clean_val = str(val).replace('$', '').replace(',', '').strip()
                        val = float(clean_val)
                except (ValueError, TypeError):
                    val = 0.0
            
            if internal_field == 'es_peso':
                if isinstance(val, str):
                    val = val.lower() in ['yes', '1', 'true', 'si']
                elif isinstance(val, (int, float)):
                    val = bool(val)
            
            mapped[internal_field] = val
        return mapped

    def commit_import(self, session: Session, context: CoreContext, data_list: List[Dict[str, Any]]) -> ServiceResponse:
        """
        Inserta la lista de productos validados en el inventario del tenant.
        """
        success_count = 0
        error_count = 0

        for item in data_list:
            try:
                d = item.get('mapped', {})
                # Llamamos al stock_service pasando la sesión inyectada
                res = stock_service.add_product(
                    session,
                    context,
                    codigo=d.get('codigo'),
                    nombre=d.get('nombre'),
                    precio=d.get('precio'),
                    cantidad=d.get('cantidad'),
                    categoria=d.get('categoria'),
                    es_peso=d.get('es_peso', False)
                )
                if res.success: success_count += 1
                else: error_count += 1
            except Exception:
                error_count += 1

        return ServiceResponse.success_res(
            data={"success": success_count, "errors": error_count}, 
            message=f"Importación finalizada. {success_count} cargados, {error_count} errores."
        )

# Singleton para acceso global
import_service = ImportService()
