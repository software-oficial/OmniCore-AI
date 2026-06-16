# 🧠 OMNICORE_STATE: Memoria de Estado del Proyecto

## 🎯 Objetivo Maestro
Construir un **SaaS Orchestrator (Business OS)** que permita a miles de desarrolladores gestionar sus aplicaciones (Stock, WhatsApp, Pagos) mediante una API de comandos coordinados. 
- **Soberanía de Datos:** El sistema NO crea ni gestiona bases de datos. Solo coordina la lógica procesando el "ADN" (Contexto) del token y ejecutando funciones sobre la DB del cliente.
- **Código Único:** Una sola implementación de lógica de negocio servida a miles de tenants.
- **Orquestación:** Transformar procesos complejos en comandos `@command` stateless y auditables.

---

## 📍 Estado Actual
- **Arquitectura Core:** Validada. `ModuleLoader`, `CommandDispatcher` y `InfrastructureRegistry` están operativos y diseñados para escala masiva.
- **Autenticación:** Basada en JWT con resolución de infraestructura vía caché (L1/L2/L3).
- **Fase Actual:** Inicio de la **Absorción de Lógica de Valor** desde la carpeta `/contenido`.

---

## 🛠️ Hoja de Ruta (Roadmap)

### Capa A: Núcleo de Coordinación ✅
- [x] Implementar `CommandDispatcher` y `ModuleLoader`.
- [x] Definir `CoreContext` (ADN del request).
- [x] Resolver infraestructura dinámica vía tokens.

### Capa B: Absorción de Dominios (Lógica de Valor) 🚀
- [ ] **Módulo Stock:** Extraer algoritmos de inventario, alertas y ventas $ightarrow$ `@command`.
- [ ] **Módulo WhatsApp:** Extraer máquinas de estado y flujos de bot $ightarrow$ `@command`.
- [ ] **Módulo Pagos:** Extraer conciliación y flujos de pasarela $ightarrow$ `@command`.

### Capa C: Gobernanza y Seguridad ⏳
- [ ] Migrar validaciones de permisos al Token (JWT).
- [ ] Implementar auditoría de ejecución stateless.
- [ ] Definir Tiers de acceso (FREE, PRO, ENTERPRISE).

### Capa D: Validación y Stress Test ⏳
- [ ] Simulación de carga masiva (1,000+ tenants).
- [ ] Auditoría de latencia y fugas de memoria en pools de DB.

---

## ✍️ Estándares de Ingeniería (Correct-by-Design)

Para evitar errores de `pre-commit` y asegurar la estabilidad:

1. **Firma de Función Obligatoria:**
   `def nombre_funcion(session: Session, context: CoreContext, **params):`
2. **Soberanía de Datos:** 
   - Prohibido usar `session.commit()`. El commit es responsabilidad del Dispatcher.
   - Prohibido crear tablas o esquemas.
3. **Cero Frameworks:** 
   - No importar `fastapi`, `flask` o `request` dentro de los dominios.
4. **Retorno Estandarizado:** 
   - Siempre retornar `ServiceResponse.success_res()` o `ServiceResponse.error_res()`.
5. **Tipeo Estricto:** 
   - Uso obligatorio de `typing` para todos los argumentos y retornos.

---

## 🧠 Aprendizajes y Decisiones
- **Decisión 1:** Se elimina cualquier gestión de infraestructura de DB del núcleo. El sistema es un procesador de lógica pura.
- **Decisión 2:** Se utiliza un sistema de caché L1/L2/L3 para evitar que la resolución de infraestructura sea un cuello de botella.
- **Decisión 3:** La atomicidad de negocio se manejará mediante compensaciones, no mediante rollbacks de SQL globales.

---

## 📅 Pendientes Inmediatos
1. Analizar `contenido/plataforma-stock/src` para identificar funciones de valor.
2. Refactorizar la primera función de Stock al patrón `@command`.
3. Validar la ejecución vía API.
