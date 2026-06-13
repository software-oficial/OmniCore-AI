# 🛠️ Guía Técnica de la API OmniCore-AI

Esta guía define cómo interactuar con el Meta-Orquestador OmniCore-AI para desplegar y gestionar procesos de negocio. La API está diseñada para ser consumida tanto por Desarrolladores Humanos como por Agentes de IA.

---

## 🎯 Concepto Fundamental: El Endpoint Maestro

A diferencia de las APIs REST tradicionales con cientos de rutas, OmniCore-AI utiliza un **Dispatcher Pattern**. Existe un único punto de entrada para toda la lógica de negocio:

`POST /api/gateway/execute`

Este endpoint actúa como un proxy inteligente que valida la seguridad, inyecta la base de datos del cliente y ejecuta la función solicitada.

### 📦 Estructura de la Petición (Payload)

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :--- | :--- |
| `command` | `string` | Sí | El identificador único de la función (ej. `stock.update`). |
| `params` | `object` | Sí | Diccionario con los argumentos necesarios para la función. |

**Headers Obligatorios:**
- `Authorization`: `Bearer <TU_TOKEN_DE_AGENTE>`

---

## 📚 Mapa de Comandos Disponibles

### 📦 Módulo de Stock (`stock.*`)
- `stock.add`: Añade o actualiza un producto.
- `stock.get`: Obtiene detalles de un producto por código.
- `stock.update`: Ajusta el inventario (Suma/Resta).
- `stock.list`: Lista productos con filtros.
- `stock.history`: Retorna el Ledger de movimientos de un SKU.
- `stock.low`: Lista productos bajo el umbral crítico.
- `stock.import.preview`: Previsualiza una carga masiva de datos.
- `stock.import.commit`: Ejecuta la carga masiva en la DB.

### 💰 Módulo de Ventas y Pagos (`sales.*`, `pay.*`)
- `sales.process`: Venta directa completa (Stock $ightarrow$ Venta $ightarrow$ Caja).
- `sales.pending`: Crea una reserva de productos sin pago.
- `sales.confirm`: Confirma el pago de una venta pendiente.
- `cash.open`: Abre la jornada de caja.
- `cash.close`: Cierra caja y genera arqueo.
- `pay.mp.create`: Genera link de pago de MercadoPago.
- `pay.mp.verify`: Verifica estado de transacción externa.
- `pay.mp.refund`: Procesa devolución de dinero.

### 💬 Módulo de WhatsApp (`bot.*`, `wa.*`)
- `bot.process_message`: Entrada principal del Bot (orquestador de menús).
- `bot.state.get` / `set` / `clear`: Gestión del contexto del usuario.
- `bot.menu.list` / `get`: Administración de la estructura de menús.
- `wa.process_message`: Procesamiento básico de mensajes entrantes.

---

## 🔄 Ciclo de Vida de una Petición

1. **Auth**: El Gateway valida el token y recupera el `agent_id`.
2. **Infra Lookup**: Se busca la DB asociada a ese agente/app.
3. **Session Injection**: Se abre una sesión de SQLAlchemy específica para ese cliente.
4. **Governance Check**: Se verifica si el Plan (Tier) y los Permisos del usuario permiten ejecutar el comando.
5. **Execution**: Se ejecuta la función stateless en un hilo separado para no bloquear el sistema.
6. **Standardized Response**: Se retorna un objeto `ServiceResponse` consistente.

---

## ⚠️ Guía de Manejo de Errores

Todas las respuestas siguen este formato:
```json
{
  "success": false,
  "message": "Mensaje legible para el usuario",
  "error_code": "CODIGO_DE_ERROR",
  "data": null,
  "latency_ms": 12.45
}
```

### Códigos Críticos:
- `AUTH_TOKEN_INVALID`: Token expirado o incorrecto.
- `INFRA_NOT_FOUND`: El agente no tiene una base de datos de negocio asociada.
- `COMMAND_NOT_FOUND`: El comando solicitado no existe en el registro.
- `STOCK_INSUFFICIENT`: Intento de vender más de lo disponible.
- `GOVERNANCE_DENIED`: El plan actual del cliente no incluye esta funcionalidad.

---

## 🤖 Instrucciones para Agentes de IA (LLMs)

Si eres un Agente de IA operando OmniCore-AI:
1. **Sigue el Manifiesto**: Antes de ejecutar, consulta `bot.menu.list` o la documentación de comandos para asegurar que usas los parámetros correctos.
2. **Maneja el Estado**: Usa `bot.state.set` para recordar datos del usuario entre mensajes.
3. **Valida antes de Actuar**: Si vas a procesar una venta, ejecuta primero `stock.get` para informar al usuario sobre la disponibilidad.
4. **Learning Mode**: Si recibes un error con el prefijo `💡 MENTORSHIP`, lee la sugerencia; el sistema te está enseñando el patrón correcto de ejecución.
