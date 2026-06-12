# 🤖 OmniCore-AI: Agent Instructions (GEMINI.md)

OmniCore-AI es un Meta-Orquestador diseñado para que Agentes de IA desplieguen y gestionen infraestructuras de negocio con cero fricción.

## 🛠️ Mandatos del Sistema (Leyes Core)

1. **Soberanía de Datos (Statelessness)**: El Core NUNCA almacena datos de clientes finales. Toda la persistencia de negocio ocurre en la DB externa del desarrollador.
2. **Inyección Dinámica**: Toda función de módulo DEBE recibir la `session` de SQLAlchemy y el `CoreContext` como argumentos. No usar gestores de DB globales dentro de los módulos.
3. **Gobernanza Estricta**: Ningún comando se ejecuta sin pasar por el `GovernanceService` (Tier $ightarrow$ PBAC $ightarrow$ Entity).
4. **Respuestas Pedagógicas**: En `LEARNING_MODE`, los errores deben seguir el patrón: `Error` $ightarrow$ `Por qué ocurrió` $ightarrow$ `Ejemplo de corrección`.

## 📐 Reglas de Enrutamiento de Datos

- **Internal Registry (SQLite)**: Almacena `Agentes`, `Apps` y `Secretos de Conexión` a las DBs externas.
- **External Business DB (Postgres)**: Almacena `Productos`, `Ventas`, `Caja`, `Clientes` y `Permisos de Usuario`.

## 🔄 Flujo de Ejecución del Agente

`Request` $ightarrow$ `Token Validation` $ightarrow$ `Infrastructure Lookup` $ightarrow$ `Session Injection` $ightarrow$ `Governance Check` $ightarrow$ `Module Execution` $ightarrow$ `Standardized ServiceResponse`.

## 📈 Guía de Extensibilidad para el Agente

Para añadir nuevas capacidades al sistema:
1. **Definir el Blueprint**: Crear el SQL necesario para las tablas de negocio.
2. **Implementar la Lógica**: Crear funciones stateless que utilicen la sesión inyectada.
3. **Registrar Comando**: Vincular la función a un nombre de comando en el `CommandRegistry`.
4. **Validar Gobernanza**: Definir el Tier mínimo y la llave de permiso requerida en el `GovernanceService`.
