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

## 🛡️ Estrategia de Seguridad (Defense-in-Depth)

OmniCore-AI implementa un modelo de seguridad multicapa para neutralizar los vectores de ataque más comunes en APIs modernas:

1. **Neutralización de XSS (HTML Encoding)**: 
   En lugar de intentar filtrar etiquetas peligrosas (blacklisting), el sistema aplica un **Escapado de HTML** sistemático a todos los inputs de texto. Los caracteres `<` `>` `&` `"` `'` se convierten en sus entidades HTML correspondientes. Esto garantiza que cualquier código inyectado sea tratado como texto plano y nunca ejecutado por el navegador.

2. **Prevención de Mass Assignment (Schema Filtering)**: 
   El Gateway implementa un filtro de "lista blanca" basado en el esquema de cada comando. Si un atacante envía campos adicionales (ej. `price` en un comando de `update_stock`), el sistema los descarta automáticamente antes de que lleguen al servicio de negocio.

3. **Integridad de Datos (Strict Type Checking)**: 
   Cada comando tiene un esquema de tipos definido. El sistema valida que los datos recibidos coincidan exactamente con el tipo esperado (`int`, `float`, `string`, etc.), rechazando la petición inmediatamente si hay una discrepancia.

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
