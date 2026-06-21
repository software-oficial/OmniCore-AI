/**
 * ⚙️ Configuración del Frontend de WhatsApp
 * Cambia IS_MOCK_MODE a 'false' para conectar con un backend real.
 */
const CONFIG = {
  API_BASE_URL: 'http://localhost:8000/api', // No se usará en Mock Mode
  IS_MOCK_MODE: true,
  POLLING_INTERVAL: 5000, 
  MESSAGE_POLLING_INTERVAL: 3000,
};

window.CONFIG = CONFIG;
