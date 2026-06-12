# 🛠️ Manual de Mantenimiento y Operaciones

Este documento describe las tareas recurrentes y los procedimientos de emergencia para mantener OmniCore-AI en estado óptimo.

## 🏥 Monitoreo y Salud

### Verificación de Componentes
Utilice el endpoint de salud para verificar el estado del sistema:
`GET /health`

**Indicadores Críticos:**
- `redis: online`: El sistema de caching de gobernanza está activo.
- `db_pool_size`: Número de conexiones activas a DBs externas. Un crecimiento desmedido puede indicar fugas de sesión.
- `core_db: connected`: El registro interno es accesible.

### Logs del Sistema
- **General**: `backend.log` (o la salida de stdout del proceso).
- **Sentinel**: `backend_sentinel.log` (registra los reinicios automáticos y fallos de heartbeat).

---

## 🔄 Gestión de Actualizaciones (Safe-Update)

Para actualizar el sistema sin interrumpir el servicio, siga el flujo de **Safe-Update**:

1. **Despliegue en Sombra**: Instalar la nueva versión en un puerto temporal o entorno de staging.
2. **Validación**: Ejecutar los tests de regresión (`tests/gauntlet_test.py`).
3. **Swap Atómico**: Actualizar el enlace simbólico o cambiar el tráfico en el balanceador de carga.
4. **Rollback**: En caso de error, revertir el enlace simbólico a la versión anterior estable.

---

## 🪴 Operaciones de Base de Datos

### Seeding (Carga Inicial)
Para resetear el entorno de desarrollo o preparar un nuevo servidor:
```bash
python3 seed_omnicore.py
```
*Este comando inicializa el esquema del Core Registry y crea un agente de prueba.*

### Actualización de Blueprints
Cuando se añade una nueva tabla a un módulo de negocio:
1. Actualizar el `blueprint.sql` del módulo.
2. Ejecutar el SQL en las bases de datos de los clientes afectados.
3. El `schema_validator` de OmniCore detectará automáticamente si la DB del cliente está desactualizada y devolverá un error pedagógico.

---

## 🚨 Procedimientos de Emergencia

### El Motor no responde (Panic Mode)
Si el Sentinel no logra reiniciar el sistema:
1. Matar procesos huérfanos: `pkill -f "python3 api/main.py"`
2. Limpiar cache de Redis: `redis-cli FLUSHALL`
3. Reiniciar manualmente: `python3 api/main.py`

### Bloqueo de Conexiones (DB Saturation)
Si el `db_pool_size` es demasiado alto:
- El `pool_cleanup_worker` interno elimina pools inactivos cada 30 minutos.
- Para forzar una limpieza, reinicie el proceso del motor.
