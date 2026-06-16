# 🛡️ OmniCore Pro SDK: Arquitectura de Ejecución Delegada

Este SDK representa la solución final y optimizada para la interacción entre el Meta-Orquestador de la nube y la infraestructura privada del cliente.

## 🚀 ¿Qué resuelve este SDK?

A través de las iteraciones de desarrollo y testeo, hemos identificado y solucionado los siguientes puntos críticos:

### 1. Resiliencia al Formato de Respuesta (API-Agnostic)
La API de OmniCore puede responder de dos formas según el comando:
- **Respuesta de Datos**: Retorna una `list` directamente (ej. `stock.list`).
- **Respuesta de Control**: Retorna un `dict` con instrucciones (ej. `{"success": true, "data": {"action": "EXECUTE_LOCALLY"}}`).

El SDK Pro implementa una validación de tipo dinámica que evita el error `'list' object has no attribute 'get'`, envolviendo los datos crudos en un objeto de éxito consistente.

### 2. Modelo de Gobernanza "Cloud-First, Data-Local"
El SDK no toma decisiones sobre qué ejecutar; delega la gobernanza a la nube:
- **Nube**: Valida permisos, verifica el token y decide si el comando debe ejecutarse en el servidor o localmente.
- **SDK**: Actúa como el "músculo" que ejecuta la acción sobre la DB local solo cuando recibe la instrucción `EXECUTE_LOCALLY`.

### 3. Onboarding Robusto y Transparente
Se ha eliminado el "fallo silencioso". El nuevo método `onboard()`:
- Valida estrictamente los códigos de estado HTTP.
- Propaga errores detallados (ej. `db_password missing`) directamente al desarrollador.
- Sincroniza la identidad localmente en `.omnicore_config.json` para evitar re-autenticaciones.

### 4. Manejo de Infraestructura Híbrida
Soporta tanto `localhost` como bases de datos remotas (ej. Railway) mediante la inyección de `DATABASE_URL`, permitiendo que el mismo SDK funcione en entornos de desarrollo y producción.

## 🛠️ Guía de Uso Rápido

```python
from omnicore_sdk import OmniCoreSDK

sdk = OmniCoreSDK()

# 1. Registro y Vinculación (Solo una vez)
sdk.onboard(
    name="MiAgente", 
    platform_name="MiEmpresa", 
    db_config={"db_host": "...", "db_user": "...", "db_password": "...", "db_name": "...", "db_port": 5432}
)

# 2. Ejecución de Comandos
resultado = sdk.execute("stock.list", {"category": "electronics"})
print(resultado["data"])
```

## 📊 Comparativa de Versiones

| Característica | SDK Original | SDK Pro (Esta versión) |
| :--- | :--- | :--- |
| **Manejo de Errores** | Silencioso (`None`) | Excepciones Explícitas |
| **Tipado de Respuesta** | Solo Diccionarios | Soporte Híbrido (List/Dict) |
| **Logging** | Ausente | Integrado (Python Logging) |
| **Configuración** | Manual | Automatizada vía `onboard()` |
| **Validación** | Básica | Ruff + Mypy Validated |
