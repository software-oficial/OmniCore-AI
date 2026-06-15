# 🚀 Guía de Inicio Rápido: OmniCore-AI

Bienvenido al ecosistema OmniCore-AI. Esta guía está diseñada para que cualquier desarrollador pueda integrar el sistema en minutos, operando de forma **100% local**.

⚠️ **ADVERTENCIA CRÍTICA**: No intentes configurar túneles de red (Cloudflare, Ngrok) ni subir tu base de datos a la nube. OmniCore-AI utiliza **Ejecución Delegada**. La API Cloud coordina, pero el SDK ejecuta todo en tu máquina.

## 🛠️ 1. El Camino del Desarrollador (Flujo Local-First)

Sigue este orden estrictamente para evitar errores de configuración:

### Paso 1: El SDK (Tu Punto de Entrada)
El SDK es la llave que conecta tu entorno local con el cerebro de OmniCore.
1. **Descarga el SDK**: Utiliza el enlace de descarga oficial en `/api/sdk/download` o el botón en la Documentación.
2. **Instala** `requests sqlalchemy psycopg2-binary`.
3. **Configura** tus credenciales:
   ```python
   sdk = OmniCoreSDK()
   sdk.set_credentials(agent_id="...", token="...", app_id="...")
   ```

### Paso 2: Base de Datos Local (Soberanía de Datos)
Tú eres el dueño de tu data. El sistema solo necesita que la estructura sea la correcta.
1. **Levanta PostgreSQL** localmente.
2. **Crea una DB** vacía.
3. **Carga los Blueprints**: Ejecuta los archivos `.sql` de `src/domains/*/blueprint.sql`. 
   *Ejemplo: `psql -d my_db -f src/domains/stock/blueprint.sql`*

### Paso 3: Ejecución y Validación
Ahora puedes ejecutar comandos. El SDK se encargará de pedir permiso a la nube y ejecutar la acción en tu DB local.
- **Ejemplo**: `sdk.execute("stock.add", {"name": "Producto X", "price": 100})`

---

## 🗺️ 2. Mapa de Módulos Funcionales (Ejemplos)

### 📦 Módulo de Stock
- `stock.add`: Registra productos nuevos.
- `stock.list`: Consulta el inventario.

### 💰 Módulo de Sales
- `sales.process`: Procesa una venta completa.
- `sales.list`: Historial de transacciones.

### 🤖 Módulo de WhatsApp
- `whatsapp.bot.process_message`: El cerebro de la conversación.
- `whatsapp.bot.welcome`: Inicializa el flujo.

---

## ⚠️ 3. Reglas de Oro para el Éxito

1. **Soberanía Total**: Recuerda que la API Cloud es un puente. Tu base de datos nunca sale de tu máquina.
2. **El SDK es Obligatorio**: No intentes hacer peticiones HTTP directas al Gateway para acciones de negocio; usa el SDK para que la delegación funcione.
3. **Modo LEARNING**: Si recibes un error con el prefijo `💡 MENTORSHIP`, lee la sugerencia; el sistema te está enseñando el patrón correcto.

## 📋 4. Resumen de Herramientas

| Herramienta | Propósito | Ubicación |
| :--- | :--- | :--- |
| **OmniCore SDK** | Ejecutor Local | `src/sdk/omnicore_sdk.py` |
| **Blueprints SQL** | Esquema de Tablas | `src/domains/*/blueprint.sql` |
| **Cloud API** | Coordinador/Validador | `https://api.omnicore.ai` |
| **Manifiesto** | Filosofía de Despliegue | `docs/LOCAL_FIRST.md` |
