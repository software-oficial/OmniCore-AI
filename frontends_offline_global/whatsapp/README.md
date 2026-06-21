# 📱 WhatsApp Hub - Módulo de Desarrollo Frontend

Este es un frontend modular diseñado para integrarse con la plataforma de automatización de WhatsApp.

## ⚙️ Configuración de Integración

Para conectar este frontend con un backend real, edite el archivo `js/config.js`:

1. Cambie `IS_MOCK_MODE` de `true` a `false`.
2. Actualice `API_BASE_URL` con la dirección de su servidor.

## 🏗️ Arquitectura del Módulo

El proyecto sigue un patrón de tres capas para facilitar el mantenimiento:

- **`js/config.js`**: Variables globales y switches de modo.
- **`js/api.js`**: Capa de servicio. Encapsula todas las llamadas `fetch`. Si el modo Mock está activo, simula las respuestas del servidor.
- **`js/app.js`**: Lógica de interfaz. Se encarga del DOM y los eventos. No contiene URLs ni lógica de red.

## 🔌 Contratos de Datos Esperados (Backend)

El backend debe proporcionar los siguientes endpoints:

- `GET /conversations`: Devuelve un array de chats `[{ phone_number, name, is_human_intervening }]`.
- `GET /messages/{phone}`: Devuelve un array de mensajes `[{ sender, content, timestamp }]`.
- `POST /send_message_from_dashboard`: Recibe `{ phone_number, content }`.
- `POST /send_media_from_dashboard`: Recibe `FormData` con `file`, `phone_number` y opcionalmente `caption`.
- `POST /intervention`: Recibe `{ phone_number, status }` para cambiar entre modo Bot y Humano.
- `POST /conversations/delete`: Recibe `{ phone_number }`.
