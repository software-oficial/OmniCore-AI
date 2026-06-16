# 🛠️ Guía de Estándares para la Creación de Comandos - OmniCore-AI

Este documento define el estándar obligatorio para la implementación de nuevos comandos dentro de los módulos de negocio. El cumplimiento de estas reglas garantiza que el `ModuleLoader` registre el comando correctamente y que el `AIGateway` pueda validarlo, ejecutarlo y auditarlo sin errores.

## 1. El Decorador `@command`

Todo comando debe estar envuelto en el decorador `@command`. Este decorador proporciona la metadata necesaria para que la IA descubra la funcionalidad y el sistema valide los inputs. Gracias al sistema **ODDS (OmniCore Dynamic Discovery System)**, esta metadata se expone en tiempo real vía API.

### Parámetros del Decorador:
| Parámetro | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `name` | `string` | Sí | Identificador único. Formato sugerido: `modulo.accion` (ej: `stock.update`). |
| `description` | `string` | Sí | Descripción clara y concisa. **Es lo que la IA usa para decidir si invocar el comando.** |
| `params_model` | `Type[BaseModel]` o `dict` | Sí | Modelo de Pydantic o diccionario de parámetros esperados y sus tipos (ej: `{"codigo": "string", "cantidad": "int"}`). |
| `example` | `dict` | No | Un ejemplo real de los parámetros para el comando. **Crucial para reducir alucinaciones de la IA.** |

---

## 2. Firma de la Función (Contrato de Interfaz)

Para que la inyección de dependencias del Gateway funcione, la función **DEBE** seguir estrictamente este orden de argumentos:

```python
@command(
    name="modulo.accion",
    description="Descripción detallada para la IA",
    params_model={"param1": "tipo", "param2": "tipo"}
)
def nombre_de_la_funcion(self, session: Session, context: CoreContext, param1: Tipo, param2: Tipo) -> ServiceResponse:
    # Implementación
    return ServiceResponse.success_res(...)
```

### Detalle de Argumentos:
1.  **`self`**: Referencia a la instancia del servicio (clase).
2.  **`session: Session`**: Sesión de SQLAlchemy inyectada. Es la **única** vía de acceso a la base de datos de negocio.
3.  **`context: CoreContext`**: Objeto con metadata de la sesión (Agent ID, App ID, Tier de suscripción, Mode).
4.  **Parámetros de Negocio**: Deben coincidir exactamente en nombre y tipo con lo definido en el `params_model`.

---

## 3. Reglas de Implementación (Mandatos Core)

### ✅ A. Retorno Obligatorio (`ServiceResponse`)
Nunca retornes diccionarios, booleanos o strings directamente. Utiliza siempre la clase `ServiceResponse`:
*   **Éxito:** `ServiceResponse.success_res(data=..., message="...")`
*   **Error:** `ServiceResponse.error_res(message="...", error_code="...")`

### ✅ B. Soberanía de Datos (Statelessness)
*   **Prohibido** el uso de gestores de base de datos globales o singletons dentro de la lógica del comando.
*   Toda operación debe usar la `session` inyectada.

### ✅ C. Atomicidad y Transacciones
*   **NO ejecutar `session.commit()` ni `session.rollback()` dentro del comando.**
*   El `AIGateway` gestiona la transacción global. Si el comando es parte de un flujo (Batch), el Gateway decidirá si hacer commit de todo el grupo o rollback total.

### ✅ D. Manejo de Errores
Encapsula la lógica en bloques `try-except` y transforma las excepciones en respuestas de error controladas:
```python
except Exception as e:
    logger.error(f"Error en modulo.accion: {e}")
    return ServiceResponse.error_res(f"Error interno: {str(e)}", "MODULO_ACTION_ERROR")
```

---

## 4. Ejemplo Maestro (The Golden Example)

```python
@command(
    name="stock.update_price",
    description="Actualiza el precio de venta de un producto específico.",
    params_schema={"code": "string", "new_price": "float"}
)
def update_product_price(self, session: Session, context: CoreContext, code: str, new_price: float) -> ServiceResponse:
    try:
        # 1. Operación usando la sesión inyectada
        query = text("UPDATE products SET price = :price WHERE code = :code")
        result = session.execute(query, {"price": new_price, "code": code})
        
        # 2. Validación de resultado
        if result.rowcount == 0:
            return ServiceResponse.error_res("Producto no encontrado", "PRODUCT_NOT_FOUND")
            
        # 3. Retorno estandarizado (SIN COMMIT)
        return ServiceResponse.success_res(
            data={"code": code, "new_price": new_price},
            message=f"Precio del producto {code} actualizado exitosamente a ${new_price}."
        )
    except Exception as e:
        logger.error(f"Error actualizando precio de {code}: {e}")
        return ServiceResponse.error_res("Error interno al actualizar precio", "PRICE_UPDATE_ERROR")
```

---

## 5. Checklist de Validación Final

Antes de añadir un comando, verifica:
- [ ] ¿Tiene el decorador `@command` con `name`, `description` y `params_schema`?
- [ ] ¿La firma comienza con `(self, session, context, ...)`?
- [ ] ¿Los parámetros de la función coinciden con el `params_schema`?
- [ ] ¿Retorna siempre un `ServiceResponse`?
- [ ] ¿He eliminado cualquier `session.commit()` interno?
- [ ] ¿Usa la `session` inyectada en lugar de una conexión global?
