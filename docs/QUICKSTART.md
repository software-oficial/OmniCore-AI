# 🚀 Guía de Inicio Rápido: OmniCore-AI API

Bienvenido al ecosistema OmniCore-AI. Esta guía está diseñada para que cualquier desarrollador pueda integrar la API en minutos, evitando errores comunes y maximizando la eficiencia.

## 🛠️ 1. El Camino del Desarrollador (Flujo de Trabajo)

Para evitar errores de `MISSING_PARAMETER` o `INFRA_NOT_FOUND`, sigue siempre este orden:

### Paso 0: Infraestructura (Soberanía de Datos)
OmniCore-AI **no aloja tu base de datos de negocio**. Para que el sistema funcione, debes:
1. **Desplegar PostgreSQL**: Tener una instancia de Postgres accesible desde internet.
2. **Ejecutar Blueprints**: Importar los archivos `.sql` (ej. `src/domains/stock/blueprint.sql`) en tu base de datos para crear las tablas necesarias.
3. **Vincular**: Usar el endpoint `POST /api/agent/projects/create` enviando las credenciales de tu DB.
**⚠️ Si saltas este paso, recibirás el error `INFRA_NOT_FOUND` o errores de conexión al intentar ejecutar cualquier comando.**

### Paso A: Descubrimiento (No adivines)
Antes de enviar cualquier comando, consulta la lista de comandos reales y sus esquemas de parámetros.
- **Endpoint**: `GET /api/discovery/commands`
- **Qué obtienes**: Una lista de todos los comandos disponibles, su descripción y el JSON exacto que debes enviar en `params`.

### Paso B: Verificación de Alias
Si no estás seguro del nombre del comando (ej. ¿es `ventas.list` o `sales.list`?), consulta los alias soportados.
- **Endpoint**: `GET /api/discovery/aliases`
- **Nota**: El sistema es tolerante y traducirá automáticamente alias comunes, pero te sugerirá el nombre oficial en la respuesta.

### Paso C: Ejecución y Validación
Envía tu comando a través del Gateway.
- **Endpoint**: `POST /api/command` (o vía el Gateway de Agentes)
- **Validación Masiva**: Si cometes errores en los parámetros, la API te devolverá **todos los errores a la vez** en una sola respuesta. No tendrás que hacer múltiples llamadas para corregir un solo comando.

---

## 🗺️ 2. Mapa de Módulos Funcionales

### 📦 Módulo de Stock (Inventario)
Gestiona la disponibilidad y registro de productos.
- `stock.add`: Registra productos nuevos.
- `stock.update`: Ajusta cantidades existencias.
- `stock.list`: Consulta el inventario actual.

### 💰 Módulo de Sales (Ventas)
Procesa transacciones comerciales.
- `sales.process`: El núcleo de la venta. Requiere `customer_id`, `items` y `payment_method`.
- `sales.list`: Historial de transacciones.

### 🤖 Módulo de WhatsApp (Comunicación)
Interacción automatizada con clientes.
- `whatsapp.create_flow`: Define flujos de conversación.
- `whatsapp.send`: Envío de mensajes directos.

---

## ⚠️ 3. Reglas de Oro para evitar errores

1. **Tipado Estricto**: Si el esquema dice `int`, envía un número, no un string `"10"`. La API validará esto estrictamente.
2. **Soberanía de Datos**: Recuerda que esta API es un puente. No gestiona la base de datos del cliente directamente, sino que inyecta la sesión necesaria para operar sobre ella.
3. **Modo LEARNING**: Si usas un token de aprendizaje, verás respuestas pedagógicas que te explican **por qué** falló un comando y cómo corregirlo.

## 📋 4. Resumen de Endpoints de Utilidad

| Endpoint | Método | Propósito |
| :--- | :--- | :--- |
| `/api/discovery/commands` | `GET` | Listado oficial de comandos y parámetros. |
| `/api/discovery/aliases` | `GET` | Diccionario de alias soportados. |
| `/api/auth/login` | `POST` | Obtención de token JWT. |
| `/health` | `GET` | Estado de salud del sistema y Redis. |
