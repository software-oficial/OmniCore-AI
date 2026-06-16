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

## 🤖 Bootstrapping para Agentes de IA (LLMs)

Si eres un Agente de IA, ya no necesitas depender de documentación estática. OmniCore-AI implementa el **OmniCore Dynamic Discovery System (ODDS)**, transformando la API en un sistema auto-descriptivo. Sigue este flujo de auto-aprendizaje para operar con precisión:

### 1. Fase de Descubrimiento Dinámico (The ODDS Loop)
Antes de realizar cualquier acción de negocio, debes realizar una introspección del sistema en tiempo real:

- **Introspección de Esquema**: `GET /api/discovery/schema` $\rightarrow$ Te devuelve el mapa real y actual de tablas y columnas de la base de datos de negocio. Úsalo para entender qué campos existen antes de intentar leer o escribir datos.
- **Catálogo de Comandos**: `GET /api/discovery/commands` $\rightarrow$ Lista todas las capacidades disponibles y sus descripciones.
- **Inspección de Contrato**: `GET /api/gateway/inspect/{command}` $\rightarrow$ Te proporciona el contrato exacto de un comando: parámetros requeridos, opcionales, tipos de datos y un **ejemplo de valor válido**.
- **Especificación Técnica**: `GET /api/gateway/openapi` $\rightarrow$ Proporciona el esquema OpenAPI 3.0 completo.

### 2. Ciclo de Ejecución y Auto-Corrección
Para cada acción, sigue este patrón:
1. **Descubrir**: Consulta el esquema de DB y el contrato del comando.
2. **Ejecutar**: Envía la petición a `/api/gateway/execute`.
3. **Corregir**: Si recibes un error con el prefijo `💡 SEMANTIC ERROR`, lee la sugerencia. El sistema analizará la base de datos y te sugerirá el nombre correcto de la columna o parámetro que intentaste usar.

### 3. Gestión de Memoria y Estado
OmniCore-AI es stateless, pero ofrece herramientas de persistencia para el bot:
- Usa `whatsapp.bot.state.set` para guardar información del usuario (nombre, preferencias, carrito).
- Usa `whatsapp.bot.state.get` al inicio de cada turno para recuperar el contexto.

---

## 📚 Mapa de Comandos Disponibles (Ejemplos)

*Nota: La lista completa y actualizada siempre estará disponible en `/api/gateway/help`.*

### 📦 Módulo de Stock (`stock.*`)
- `stock.add`: Añade o actualiza un producto.
- `stock.get`: Obtiene detalles de un producto por código.
- `stock.update`: Ajusta el inventario (Suma/Resta).
- `stock.list`: Lista productos con filtros.
- `stock.history`: Retorna el Ledger de movimientos de un SKU.
- `stock.low`: Lista productos bajo el umbral crítico.
- `stock.import.preview`: Previsualiza una carga masiva de datos.
- `stock.import.commit`: Ejecuta la carga masiva en la DB.

### 💰 Módulo de Ventas y Pagos (`sales.*`)
- `sales.process`: Venta directa completa (Stock $\rightarrow$ Venta $\rightarrow$ Caja).
- `sales.pending`: Crea una reserva de productos sin pago.
- `sales.confirm`: Confirma el pago de una venta pendiente.
- `sales.cash.open`: Abre la jornada de caja.
- `sales.cash.close`: Cierra caja y genera arqueo.
- `sales.pay.mp.create`: Genera link de pago de MercadoPago.
- `sales.pay.mp.verify`: Verifica estado de transacción externa.
- `sales.pay.mp.refund`: Procesa devolución de dinero.

### 💬 Módulo de WhatsApp (`whatsapp.*`)

Este módulo implementa un motor de conversación con **Persistencia de Estado Híbrida** (Redis + DB Tenant).

**Comandos de Orquestación (El Cerebro):**
- `whatsapp.bot.process_message`: Entrada principal. Analiza el texto, verifica el estado actual y delega la acción.
- `whatsapp.bot.navigate`: Mueve al usuario a un menú específico y persiste el cambio de estado.
- `whatsapp.bot.welcome`: Inicializa la conversación y posiciona al usuario en el menú principal.
- `whatsapp.bot.show_menu`: Muestra el contenido de un menú sin alterar el estado actual.
- `whatsapp.bot.set_human_mode` / `whatsapp.bot.set_bot_mode`: Activa o desactiva la intervención humana.

**Gestión de Estado y Menús:**
- `whatsapp.bot.state.get` / `set` / `clear`: Manipulación directa del contexto efímero del usuario.
- `whatsapp.bot.menu.list` / `get`: Consultas sobre la estructura de navegación configurada.
- `whatsapp.service.process_message`: Gateway de bajo nivel para el procesamiento de payloads raw.

---

## 🗄️ Requisitos de Infraestructura (Soberanía de Datos del Desarrollador)

**IMPORTANTE**: OmniCore-AI es un orquestador stateless. **Tú eres el dueño y gestor de tu base de datos de negocio**. El sistema no provisiona bases de datos automáticamente.

### 🚀 Guía de Montaje del SaaS en tu Servidor

Para poner en marcha tu instancia de negocio conectada a OmniCore-AI, sigue este flujo:

1. **Despliegue de DB**: Levanta una instancia de **PostgreSQL** (en Railway, AWS, Supabase, o tu propio VPS).
2. **Ejecución de Blueprints**: Ejecuta los scripts SQL proporcionados en la carpeta `src/domains/*/blueprint.sql` dentro de tu base de datos. Esto creará la estructura de tablas necesaria para que los módulos de Stock, Ventas y Bot funcionen.
3. **Vinculación de Proyecto**: Llama al endpoint `POST /api/agent/projects/create` enviando el nombre de tu proyecto y las credenciales de conexión de tu base de datos (`db_host`, `db_port`, `db_user`, `db_password`, `db_name`).
4. **Operación**: Comienza a consumir la API utilizando el `app_id` generado. El Gateway se encargará de inyectar la sesión hacia tu servidor de base de datos en cada petición.

### 🛠️ Tablas Obligatorias (Ejemplos)
El sistema fallará si no existen las tablas definidas en los blueprints. Por ejemplo, el Bot de WhatsApp requiere:
- `bot_states`: Para persistencia de contexto.
- `whatsapp_menus` y `whatsapp_menu_options`: Para la navegación dinámica.

*Si recibes el error `INFRA_NOT_FOUND`, significa que el proyecto no ha sido vinculado correctamente o las credenciales son inválidas.*

---

## ⚙️ Flujo Interno de Ejecución

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
1. **Sigue el Manifiesto**: Antes de ejecutar, consulta `/api/gateway/help` para asegurar que usas los parámetros correctos.
2. **Maneja el Estado**: Usa `bot.state.set` para recordar datos del usuario entre mensajes.
3. **Valida antes de Actuar**: Si vas a procesar una venta, ejecuta primero `stock.get` para informar al usuario sobre la disponibilidad.
4. **Learning Mode**: Si recibes un error con el prefijo `💡 MENTORSHIP`, lee la sugerencia; el sistema te está enseñando el patrón correcto de ejecución.
