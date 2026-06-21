# 📦 Stock Pro - Módulo de Desarrollo Frontend

Este es un frontend modular diseñado para la gestión de inventario y ventas (Stock & Scan).

## ⚙️ Configuración de Integración

Para conectar este frontend con un backend real, edite el archivo `js/config.js`:

1. Cambie `IS_MOCK_MODE` de `true` a `false`.
2. Actualice `API_BASE` con la dirección de su servidor.

## 🏗️ Arquitectura del Módulo

El proyecto sigue un patrón de tres capas:

- **`js/config.js`**: Variables globales, temas y modo de simulación.
- **`js/api.js`**: Capa de Servicio. Implementa el `StockAPI` que gestiona los comandos enviados al servidor.
- **`js/app.js`**: Lógica de UI. Maneja el estado de la aplicación, las vistas y el carrito de compras.

## 🔌 Contratos de Datos Esperados (Backend)

Este frontend utiliza un patrón de **Comandos**. El servidor debe recibir un objeto JSON con un `command` y un objeto `params`.

Ejemplos de comandos:

- `auth.login`: `{ username, password }`
- `stock.list`: `{ filter }`
- `venta.add`: `{ codigo }`
- `venta.cobrar`: `{ items: [] }`
- `caja.status`: `{}`
