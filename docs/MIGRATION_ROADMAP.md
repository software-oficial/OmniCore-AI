# 🗺️ Hoja de Ruta de Migración: Refs $ightarrow$ Domains

Este documento sirve como registro maestro y checklist del proceso de migración de la lógica de negocio desde las carpetas de referencia (`refs/`) hacia la arquitectura de dominios de OmniCore-AI (`src/domains/`).

**Objetivo:** Asegurar que ninguna funcionalidad legada se pierda y que toda sea transformada al patrón de Comandos Stateless.

---

## 📊 Estado Global de Migración
- [x] **WhatsApp Domain**: 100%
- [x] **Sales Domain**: 100%
- [x] **Stock Domain**: 100%

---

## 🛠️ Detalle de Tareas de Migración

### 💬 WhatsApp Domain
**Origen:** `refs/plataforma-whatsapp/`
- [x] **Análisis**: Mapear `bot_core` y `services` a comandos stateless.
- [x] **Blueprint**: Definir tablas de contactos, mensajes y configuraciones de bot.
- [x] **Implementación**: 
ightarrow$ `whatsapp.send_text`
ightarrow$ `whatsapp.upload_media`
ightarrow$ `whatsapp.send_media`
ightarrow$ `whatsapp.set_human_mode`
ightarrow$ `whatsapp.get_status`
ightarrow$ `whatsapp.handle_bot_flow`
- [ ] **Gobernanza**: Definir permisos para gestión de bots y lectura de chats.
- [ ] **Validación**: Test de flujo completo desde el webhook hasta el comando.

### 📦 Stock Domain
**Origen:** `refs/plataforma-stock/`
- [x] **Análisis**: Descomponer `src/commands/` y `src/core/` en la nueva estructura de dominios.
- [x] **Blueprint**: Definir tablas de inventario, productos y auditoría de stock.
- [x] **Implementación**:
    - [x] Migrar el HAL (Hardware Abstraction Layer) si es necesario para escaneo.
    - [x] Migrar `audit_production.py` $\rightarrow$ `stock.audit_inventory`
    - [x] Implementar comandos de ajuste de stock y traspasos.
    - [x] Implementar `stock.import_with_mapping` (Importador inteligente)
- [x] **Gobernanza**: Definir Tiers de acceso para almaceneros vs administradores.
- [x] **Validación**: Ejecutar `test_master.py` adaptado al nuevo Core.

### 💰 Sales Domain
**Origen:** `refs/plataforma-mercado-pago/`
- [x] **Análisis**: Extraer lógica de pagos y webhooks de `api-fundacion-idear-webhook` y `bot-manager`.
- [x] **Blueprint**: Definir tablas de transacciones, órdenes y conciliaciones.
- [x] **Implementación**:
    - [x] Migrar procesamiento de Webhooks MP $\rightarrow$ `sales.handle_mp_webhook` (Automatización de pagos)
    - [x] Migrar validación de pagos $\rightarrow$ `sales.verify_payment`
    - [x] Migrar flujo de onboarding y tokens.
    - [x] Implementar `user.grant_permission` (Permisos granulares)
    - [x] Implementar `user.revoke_permission` (Revocar permisos granulares)
- [x] **Gobernanza**: Definir permisos críticos para devoluciones y ajustes financieros.
- [x] **Validación**: Simular flujo de pago y verificar persistencia en DB externa.

### ⚙️ System Domain (Core)
**Origen:** `refs/plataforma-stock/src/core/system_service.py` y `sentinel_service.py`
- [x] **Implementación**:
    - [x] Implementar `system.get_version` (Introspección de versión)
    - [x] Implementar `system.set_maintenance` (Modo mantenimiento)
    - [x] Implementar `system.validate_blueprint` (Validación de estructura DB)
- [x] **Gobernanza**: Definir permisos para comandos administrativos.
- [x] **Validación**: Simular chequeos de salud y cambio de modo. 

---

## 🏁 Criterios de Aceptación (Definition of Done)
Para marcar una tarea como completada, debe cumplir:
1. **Stateless**: La función no depende de variables globales; usa la `session` inyectada.
2. **Documentada**: El comando tiene un `params_schema` claro y descripción pedagógica.
3. **Gobernada**: El comando está registrado en el `GovernanceService`.
4. **Verificada**: Existe un test automatizado que valida el flujo en un entorno de staging.
