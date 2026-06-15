# 🚀 OmniCore-AI: Manifiesto Local-First

Si eres un desarrollador integrando OmniCore-AI, lo primero que debes entender es que **este sistema no funciona como una API tradicional**. No somos una base de datos en la nube a la que te conectas; somos un **Coordinador de Ejecución**.

## 🗝️ La Regla de Oro: El SDK es la Llave
Para operar OmniCore-AI, **debes descargar y utilizar el SDK**. 

El SDK no es una "librería opcional"; es el **Agente Ejecutor** que reside en tu máquina. Si intentas interactuar con la API sin el SDK, sentirás que "falta algo". El SDK es el que cierra el círculo entre la nube y tu entorno local.

## 🛠️ ¿Por qué no necesitas Cloudflare, Ngrok ni DBs Online?

Muchos desarrolladores cometen el error de intentar "abrir" su máquina al mundo para que la API pueda ver su base de datos. **ESTO ES UN ERROR.**

### El Flujo de Ejecución Delegada:
1. **Tu App** $ightarrow$ Envía comando al $ightarrow$ **SDK Local**.
2. **SDK Local** $ightarrow$ Consulta permiso a $ightarrow$ **OmniCore Cloud API**.
3. **OmniCore Cloud API** $ightarrow$ Responde $ightarrow$ **SDK Local**: *"Permiso concedido. Ejecuta esto en tu DB local"*.
4. **SDK Local** $ightarrow$ Escribe/Lee de $ightarrow$ **Tu Base de Datos Local**.

**Conclusión**: La API Cloud nunca toca tu base de datos. El dato nunca sale de tu máquina. No hay túneles, no hay puertos abiertos, no hay riesgos de seguridad externa.

## 📉 El Camino Mínimo Viable (MVP)
Si quieres que el sistema funcione en 5 minutos, solo necesitas:
1. **PostgreSQL Local** (Instalado y corriendo).
2. **Blueprints SQL** (Ejecutados en tu DB para crear las tablas).
3. **OmniCore SDK** (Configurado con tu `agent_id` y `token`).

Si el SDK no es suficiente para tu caso de uso avanzado, eres libre de configurar tu propio entorno, pero el SDK es el estándar mínimo para que el sistema sea operable.
