import asyncio
import logging

from src.core.module_loader import module_loader

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CommandAuditor")


async def run_audit():
    # 1. Cargar todos los módulos de dominio
    logger.info("🔍 Iniciando auditoría de comandos...")
    for module in ["sales", "stock", "whatsapp"]:
        module_loader.load_module(module)

    registry = module_loader._command_registry
    logger.info(f"✅ Total de comandos registrados: {len(registry)}")

    # 2. Iterar sobre todos los comandos
    # Nota: La ejecución real de comandos requiere contexto (session, business_id).
    # Esta auditoría verifica la integridad del registro y metadatos.
    for cmd_name, metadata in registry.items():
        logger.info(f"Checking: {cmd_name}")
        try:
            handler = metadata["handler"]
            desc = metadata["description"]
            params = metadata["params_model"]

            # Verificación básica
            if not handler or not desc:
                logger.error(f"❌ Comando {cmd_name} incompleto")
            else:
                logger.info(f"  - OK: {desc}")
                if params:
                    logger.info(f"  - Params: {params}")
        except Exception as e:
            logger.error(f"❌ Error auditando {cmd_name}: {e}")

    logger.info("🎉 Auditoría completada.")


if __name__ == "__main__":
    asyncio.run(run_audit())
