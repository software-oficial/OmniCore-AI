import { UI_CONSTANTS } from './config.js';

/**
 * 🔔 Modern Toast System
 * Sistema de notificaciones simple y elegante para todos los módulos.
 */
export const Toast = {
  /**
   * Inicializa el contenedor de toasts si no existe.
   * @returns {HTMLElement} El contenedor de toasts.
   */
  init() {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  },

  /**
   * Muestra una notificación en pantalla.
   * @param {string} message - El mensaje a mostrar.
   * @param {'success'|'error'|'info'|'warning'} type - El tipo de notificación.
   * @param {number} [duration=3000] - Duración en ms.
   */
  show(message, type = 'info', duration = 3000) {
    this.init();
    const container = document.getElementById('toast-container');
    console.log('Toast: Creando notificación...', message);

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
            <span>${message}</span>
            <button style="background:none; border:none; color:white; cursor:pointer; font-size:1.2rem; margin-left:1rem;">&times;</button>
        `;

    toast.onclick = () => this.remove(toast);
    toast.querySelector('button').onclick = (e) => {
      e.stopPropagation();
      this.remove(toast);
    };

    container.appendChild(toast);
    console.log('Toast: Elemento inyectado en:', container);

    setTimeout(() => {
      this.remove(toast);
    }, duration);
  },

  /**
   * Elimina un toast con animación.
   * @param {HTMLElement} toast - El elemento del toast a eliminar.
   */
  remove(toast) {
    toast.classList.add('toast-out');
    toast.addEventListener('animationend', () => {
      toast.remove();
    });
  },
};

// Exponer globalmente
window.Toast = Toast;
window.showToast = (msg, type) => Toast.show(msg, type);
