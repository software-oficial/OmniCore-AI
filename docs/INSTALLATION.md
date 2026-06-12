# 🛠️ Guía de Instalación y Despliegue

Esta guía detalla el proceso para levantar un entorno completo de OmniCore-AI, desde la infraestructura de base de datos hasta la capa de orquestación.

## 🏗️ Arquitectura de Datos
OmniCore-AI utiliza una arquitectura de base de datos híbrida:
1. **Core Registry (Internal)**: Almacena agentes, aplicaciones y configuraciones de infraestructura. (Recomendado: Postgres o SQLite).
2. **Business DBs (External)**: Bases de datos independientes para cada cliente/app donde reside la data de negocio. (Obligatorio: Postgres).

## 🚀 Paso a Paso: Instalación Local

### 1. Infraestructura de Soporte
Asegúrese de tener corriendo los siguientes servicios:
- **PostgreSQL**: Puerto `5432` (estándar).
- **Redis**: Puerto `6379` (estándar).

### 2. Configuración del Entorno
Cree un archivo `.env` en la raíz del proyecto con las siguientes variables:
```env
# Core Registry
OMNICORE_INTERNAL_DB_URL=postgresql://user:pass@localhost:5432/omnicore_registry

# Cache & Sessions
REDIS_HOST=localhost
REDIS_PORT=6379

# API Settings
HOST=0.0.0.0
PORT=8000
VERSION=1.0.0
```

### 3. Dependencias y Setup
```bash
# Instalar dependencias
pip install -r requirements.txt

# Inicializar el esquema del Core y crear datos de prueba
python3 seed_omnicore.py
```

### 4. Ejecución del Sistema
El sistema consta de dos procesos principales que deben correr simultáneamente:

**A. El Motor (API Gateway):**
```bash
export PYTHONPATH=.
nohup python3 api/main.py > backend.log 2>&1 &
```

**B. El Sentinel (Watchdog):**
El Sentinel monitorea el `/api/heartbeat` y reinicia el motor si falla.
```bash
python3 system_ops/sentinel_worker.py
```

---

## 🧪 Configuración de Entorno de Pruebas (SIT)
Para probar el sistema rápidamente sin configurar manualmente cada DB de negocio, utilice los scripts de automatización:

1. **Setup de Infra de Test**:
   ```bash
   python3 setup_test_infra.py
   ```
   *Este script crea un agente, una app y registra la infraestructura en el Core Registry.*

2. **Validación de Salud**:
   ```bash
   curl http://localhost:8000/health
   ```

## ☁️ Despliegue en Railway
OmniCore-AI está optimizado para Railway:
1. Conecte su repositorio a Railway.
2. Añada los servicios de **PostgreSQL** y **Redis** desde el Marketplace.
3. Configure las variables de entorno en la pestaña `Variables` usando los valores proporcionados por Railway (`${{Postgres.DATABASE_URL}}`, etc.).
4. El `Procfile` ya está configurado para iniciar el servidor FastAPI.
