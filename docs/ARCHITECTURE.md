# 📐 Arquitectura Técnica de OmniCore-AI

OmniCore-AI no es una aplicación monolítica, sino un **Meta-Orquestador** basado en patrones de resiliencia industrial.

## 🔄 Flujo de Ejecución (The Dispatcher Pattern)

Toda petición sigue un camino estrictamente gobernado para garantizar la seguridad y el aislamiento:

`Request` $ightarrow$ `Sanitization` $ightarrow$ `Token Validation` $ightarrow$ `Infra Lookup` $ightarrow$ `Type & Param Filter` $ightarrow$ `Session Injection` $ightarrow$ `Governance Check` $ightarrow$ `Module Execution` $ightarrow$ `Standardized Response`

### Componentes Clave:
1. **AIGateway (`core/dispatcher/gateway.py`)**: El punto de entrada. Coordina la sanitización, valida el token, filtra parámetros según el esquema y gestiona el ciclo de vida de la petición.
2. **GovernanceService (`core/governance/governance_service.py`)**: El "filtro" de seguridad.
   - **SaaS Tiers**: Verifica si el plan del cliente permite el comando.
   - **PBAC**: Valida permisos granulares en la DB externa del cliente.
   - **Entity Check**: Restringe comandos según el origen (ej. Bot vs Panel Admin).
3. **DynamicDbManager (`infra/db/db_manager.py`)**: El gestor de conexiones.
   - **Multi-tenancy**: Crea pools de conexión dinámicos por aplicación.
   - **Circuit Breaker**: Si una DB externa falla repetidamente, el manager "abre el circuito" y rechaza peticiones inmediatamente para no saturar el Core.
   - **Concurrency Control**: Semáforos globales para evitar que un solo cliente agote los recursos del sistema.

---

## 🗄️ Arquitectura de Datos (Modelo BYODB)

OmniCore-AI opera bajo un modelo de **Soberanía de Datos Absoluta**. Para garantizar la privacidad, seguridad y escalabilidad, implementamos el patrón **BYODB (Bring Your Own Database)**.

### 1. Core Registry (Infraestructura OmniCore)
Es la base de datos interna del sistema. Gestiona únicamente la "capa de control":
- **Agentes**: Identidades de los desarrolladores/empresas.
- **Aplicaciones**: Mapeo de agentes a proyectos.
- **Infraestructura**: Credenciales de conexión (host, puerto, user, pass) hacia las DBs externas.
- **SaaS Tiers**: Control de planes y límites de uso.

### 2. Business DB (Infraestructura del Desarrollador)
Es la base de datos donde reside toda la operación comercial. **OmniCore-AI no crea ni aloja esta base de datos**. El desarrollador es responsable de:
- **Alojamiento**: Desplegar una instancia de PostgreSQL.
- **Esquema**: Ejecutar los `blueprints.sql` proporcionados por OmniCore para crear las tablas necesarias (Stock, Ventas, Bot, etc.).
- **Conectividad**: Configurar los firewalls para que el Core de OmniCore pueda alcanzar su servidor.

### 🔄 Flujo de Vinculación de Datos

`Desarrollador` $\rightarrow$ `Crea DB Postgres` $\rightarrow$ `Ejecuta Blueprints SQL` $\rightarrow$ `Vincula Credenciales vía API (/projects/create)` $\rightarrow$ `OmniCore Inyecta Sesión Dinámica` $\rightarrow$ `Ejecución de Negocio`

Este diseño garantiza que si el desarrollador desea migrar su negocio, simplemente se lleva su base de datos; OmniCore es solo el motor de ejecución inteligente.

---

## 🛡️ Capa de Resiliencia (The Sentinel Pattern)

Para garantizar un uptime de grado empresarial, OmniCore-AI implementa el **Sentinel Pattern**:

- **OmniSentinel (`system_ops/sentinel_worker.py`)**: Un proceso independiente que actúa como Watchdog.
- **Heartbeat Mechanism**: El Sentinel consulta `/api/heartbeat` cada 2 segundos.
- **Auto-Recovery**: Si el heartbeat falla $X$ veces, el Sentinel ejecuta un script de reinicio (`restart_backend.sh`) que limpia procesos huérfanos y levanta el motor nuevamente.

---

## 📦 Modelo de Extensibilidad (Módulos)

El sistema es modular por diseño. Para añadir una nueva capacidad de negocio:
1. **Blueprint**: Definir el SQL en `modules/<name>/blueprint.sql`.
2. **Lógica con Auto-Descubrimiento**: Crear funciones stateless en el servicio del módulo (ej. `modules/<name>/sales_service.py`) y marcarlas con el decorador `@command`.
   - El decorador define el nombre del comando, la descripción y el esquema de parámetros.
   - El `ModuleLoader` detecta automáticamente estas funciones al cargar el módulo, eliminando la necesidad de archivos de registro manuales.
3. **Gobernanza**: Definir el Tier mínimo y la llave de permiso requerida en el `GovernanceService`.

Este diseño permite que el sistema sea **Stateless**, ya que el Core no conoce la estructura de los datos de negocio, solo sabe cómo inyectar la sesión y ejecutar la lógica.
