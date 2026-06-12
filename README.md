# 🌌 OmniCore-AI: The AI-Ready Business OS

OmniCore-AI es un **Meta-Orquestador de Negocios** de grado empresarial, diseñado para permitir que Agentes de IA y Desarrolladores desplieguen, gestionen y escalen múltiples instancias de SaaS (Stock, Ventas, Pagos) con infraestructura **Zero-Touch**.

## 🎯 Objetivos del Sistema
El objetivo principal de OmniCore-AI es eliminar la fricción entre la inteligencia artificial y la ejecución de procesos de negocio reales. Actúa como un "Sistema Operativo" que abstrae la complejidad de la infraestructura, la seguridad y la persistencia, permitiendo que la IA se concentre en la lógica de negocio.

### Pilares Estratégicos
- **Soberanía de Datos (Statelessness)**: El Core no almacena datos de clientes finales; cada instancia de negocio reside en su propia base de datos externa.
- **Gobernanza Dinámica**: Control de acceso basado en Tiers (Planes), PBAC (Permisos) y Restricciones de Entidad.
- **Resiliencia Industrial**: Implementación de Circuit Breakers, Global Concurrency Control y un Watchdog externo (Sentinel).
- **Interoperabilidad AI-First**: Manifiestos semánticos y un "Learning Mode" para facilitar la adopción por parte de LLMs.

---

## 🛠️ Funcionalidades Core

### 1. Orquestación de Infraestructura
- **Dynamic DB Injection**: Inyección en tiempo real de sesiones de base de datos basadas en el contexto del agente.
- **Infrastructure Registry**: Mapeo centralizado de agentes $ightarrow$ aplicaciones $ightarrow$ credenciales de DB.
- **Blueprints Dinámicos**: Despliegue de esquemas de negocio mediante scripts SQL modulares.

### 2. Motor de Gobernanza (3 Capas)
- **SaaS Tiers**: Bloqueo de funcionalidades según el plan (`FREE`, `PRO`, `ENTERPRISE`).
- **PBAC**: Control granular mediante llaves de permiso (`permission_key`) validadas contra el rol del usuario.
- **Entity Restriction**: Restricción de comandos críticos a interfaces específicas (ej. `cash.close` solo vía WEB/CLI).

### 3. Capa de Resiliencia y SRE
- **Circuit Breaker**: Suspensión automática de conexiones a DBs fallidas para evitar el colapso del sistema.
- **Dynamic Pooling**: Ajuste de tamaño de pool de conexiones según el Tier del cliente.
- **OmniSentinel**: Monitor externo que garantiza el uptime mediante reinicios automáticos basados en heartbeats.

---

## 🚀 Guía de Inicio Rápido

### Requisitos Previos
- **Python 3.10+**
- **PostgreSQL** (Para el registro core y bases de datos de negocio)
- **Redis** (Para caching de gobernanza y sesiones)

### Instalación Básica
1. **Clonar y Configurar**:
   ```bash
   git clone <repo_url>
   cd OmniCore-AI
   pip install -r requirements.txt
   cp .env.example .env # Configurar variables de entorno
   ```
2. **Inicializar Base de Datos**:
   ```bash
   python3 seed_omnicore.py
   ```
3. **Lanzar el Motor**:
   ```bash
   export PYTHONPATH=.
   python3 api/main.py
   ```
4. **Activar Sentinel (Watchdog)**:
   ```bash
   python3 system_ops/sentinel_worker.py
   ```

---

## 📖 Documentación Detallada
Para profundizar en el sistema, consulta la carpeta `/docs`:
- [**INSTALLATION.md**](docs/INSTALLATION.md): Guía paso a paso de despliegue y configuración.
- [**ARCHITECTURE.md**](docs/ARCHITECTURE.md): Detalle del Dispatcher Pattern, Sentinel y flujo de datos.
- [**MAINTENANCE.md**](docs/MAINTENANCE.md): Operaciones de mantenimiento, seeding y updates.
- [**LEARNING_STRATEGY.md**](docs/LEARNING_STRATEGY.md): Cómo entrenar agentes para usar OmniCore-AI.

---

## 🛠️ Stack Técnico
- **Backend**: FastAPI, SQLAlchemy (Async/Sync), Pydantic.
- **Infraestructura**: PostgreSQL, Redis, SQLite.
- **Operaciones**: Docker, Railway, Bash.
- **Seguridad**: JWT, PBAC, Tier-based Access.
