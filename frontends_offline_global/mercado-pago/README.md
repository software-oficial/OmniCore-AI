# 💳 Mercado Pago Gateway - Módulo de Desarrollo Frontend

Este es un frontend modular para la gestión de pasarela de pagos y control de licencias.

## ⚙️ Configuración de Integración

Para conectar este frontend con un backend real, edite el archivo `js/config.js`:

1. Cambie `IS_MOCK_MODE` de `true` a `false`.
2. Actualice `API_BASE` con la dirección de su servidor.

## 🏗️ Arquitectura del Módulo

El proyecto utiliza una arquitectura desacoplada:

- **`js/config.js`**: Configuración global y switch de modo simulación.
- **`js/api.js`**: Capa de Servicio (`PaymentAPI`). Centraliza todas las peticiones HTTP y gestiona los datos mock.
- **`js/app.js`**: Lógica de Interfaz. Gestiona la navegación entre secciones, modales y formularios.

## 🔌 Contratos de Datos Esperados (Backend)

El backend debe implementar los siguientes endpoints:

- `GET /clients`: Lista de clientes con sus estados y módulos activos.
- `PATCH /clients/{id}/status`: Cambiar estado (activo/suspendido).
- `POST /provision`: Activar cliente en múltiples plataformas.
- `GET /payments/{clientId}`: Historial de pagos de un cliente específico.
- `GET /payments/all`: Monitoreo global de todos los pagos.
- `GET /subscriptions/{clientId}`: Planes recurrentes del cliente.
- `GET /api/master/license/audit/{tenantId}`: Auditoría de servicios activos para el Master Control.
