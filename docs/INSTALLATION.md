# 🛠️ Guía de Instalación y Despliegue

Esta guía detalla cómo configurar tu entorno local para operar con OmniCore-AI. 

**IMPORTANTE**: Antes de empezar, lee el [Manifiesto Local-First](LOCAL_FIRST.md). OmniCore-AI utiliza **Ejecución Delegada**, lo que significa que no necesitas túneles de red ni bases de datos online.

## 🚀 Paso 1: Instalación del SDK (Obligatorio)
El SDK es el agente que ejecuta los comandos en tu máquina. Sin él, el sistema no es operable.

1. **Descarga el SDK**: Descarga el archivo oficial desde la API: `GET /api/sdk/download` o a través del botón de descarga en el Panel de Documentación.
2. **Instala dependencias**:
   ```bash
   pip install requests sqlalchemy psycopg2-binary
   ```
3. **Configuración**: Inicializa el SDK con tus credenciales:
   ```python
   from omnicore_sdk import OmniCoreSDK
   sdk = OmniCoreSDK()
   sdk.set_credentials(agent_id="TU_ID", token="TU_TOKEN", app_id="TU_APP_ID")
   ```

## 🏗️ Paso 2: Base de Datos Local (Soberanía de Datos)
OmniCore-AI no aloja tu data. Tú gestionas tu propia base de datos de negocio localmente.

1. **Instalar PostgreSQL**: Asegúrate de tener Postgres corriendo en tu máquina (puerto `5432`).
2. **Crear Base de Datos**: Crea una base de datos vacía (ej: `omnicore_biz`).
3. **Ejecutar Blueprints**: Importa los esquemas SQL proporcionados en `src/domains/*/blueprint.sql` para crear las tablas necesarias.
   ```bash
   psql -U usuario -d omnicore_biz -f src/domains/stock/blueprint.sql
   ```

---

## ⚙️ Configuración Avanzada (Para Administradores del Motor)
*Esta sección es solo si deseas desplegar tu propia instancia del motor de OmniCore-AI en lugar de usar la Cloud API.*

### 1. Infraestructura de Soporte
- **PostgreSQL**: Puerto `5432`.
- **Redis**: Puerto `6379`.

### 2. Configuración del Entorno (`.env`)
```env
OMNICORE_INTERNAL_DB_URL=postgresql://user:pass@localhost:5432/omnicore_registry
REDIS_HOST=localhost
REDIS_PORT=6379
HOST=0.0.0.0
PORT=8000
VERSION=1.0.0
```

### 3. Ejecución del Motor y Sentinel
```bash
pip install -r requirements.txt
python3 seed_omnicore.py
export PYTHONPATH=.
nohup python3 api/main.py > backend.log 2>&1 &
python3 system_ops/sentinel_worker.py
```

## ☁️ Despliegue en Railway
Para desplegar la infraestructura del motor en Railway, conecta tu repositorio y configura las variables de entorno proporcionadas por Railway en la pestaña `Variables`. El `Procfile` ya está configurado.
