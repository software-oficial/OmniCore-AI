/**
 * ⚙️ Configuración Global del Sistema
 * Centraliza todas las constantes y configuraciones para evitar "magic strings".
 */

export const CONFIG = {
  API_BASE_URL: '/api',
  TIMEOUT: 5000,
  THEME_DEFAULT: 'light',
  LANG_DEFAULT: 'es',
  VERSION: '1.0.0',
  // Colores semánticos adicionales si fueran necesarios
  COLORS: {
    SUCCESS: '#10b981',
    ERROR: '#ef4444',
    WARNING: '#f59e0b',
    INFO: '#3b82f6',
  },
};

export const UI_CONSTANTS = {
  TOAST_DURATION: 3000,
  MODAL_BACKDROP: 'rgba(0,0,0,0.5)',
  TRANSITION_SPEED: '0.3s',
};
