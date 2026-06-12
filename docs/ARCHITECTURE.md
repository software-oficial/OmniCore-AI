# 📐 Arquitectura Técnica de OmniCore-AI

OmniCore-AI no es una aplicación monolítica, sino un **Meta-Orquestador** basado en patrones de resiliencia industrial.

## 🔄 Flujo de Ejecución (The Dispatcher Pattern)

Toda petición sigue un camino estrictamente gobernado para garantizar la seguridad y el aislamiento:

`Request` $ightarrow$ `Token Validation` $ightarrow$ `Infra Lookup` $ightarrow$ `Session Injection` $ightarrow$ `Governance Check` $ightarrow$ `Module Execution` $ightarrow$ `Standardized Response`

### Componentes Clave:
1. **AIGateway (`core/dispatcher/gateway.py`)**: El punto de entrada. Valida el token, recupera la configuración de la DB del cliente y coordina la ejecución.
2. **GovernanceService (`core/governance/governance_service.py`)**: El "filtro" de seguridad.
   - **SaaS Tiers**: Verifica si el plan del cliente permite el comando.
   - **PBAC**: Valida permisos granulares en la DB externa del cliente.
   - **Entity Check**: Restringe comandos según el origen (ej. Bot vs Panel Admin).
3. **DynamicDbManager (`infra/db/db_manager.py`)**: El gestor de conexiones.
   - **Multi-tenancy**: Crea pools de conexión dinámicos por aplicación.
   - **Circuit Breaker**: Si una DB externa falla repetidamente, el manager "abre el circuito" y rechaza peticiones inmediatamente para no saturar el Core.
   - **Concurrency Control**: Semáforos globales para evitar que un solo cliente agote los recursos del sistema.

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
2. **Lógica**: Crear funciones stateless en `modules/<name>/sales_service.py` que reciban `(session, context, **params)`.
3. **Comandos**: Registrar la función en `modules/<name>/commands.py`.

Este diseño permite que el sistema sea **Stateless**, ya que el Core no conoce la estructura de los datos de negocio, solo sabe cómo inyectar la sesión y ejecutar la lógica.
