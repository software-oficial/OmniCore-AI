/**
 * 🤖 Auto-Icon Replacement Utility
 * Escanea el DOM y reemplaza elementos con clases de FontAwesome o atributos de datos
 * por los iconos SVG definidos en js/icons.js
 */

const IconManager = {
  // Mapeo simple de clases FontAwesome a nombres de iconos en SVG_ICONS
  map: {
    'fa-users': 'users',
    'fa-money-bill-transfer': 'cash',
    'fa-globe': 'chart',
    'fa-calendar-check': 'card',
    'fa-screwdriver-wrench': 'edit',
    'fa-plus': 'plus',
    'fa-link': 'link',
    'fa-trash': 'trash',
    'fa-credit-card': 'credit_card',
    'fa-robot': 'bot',
    'fa-comments': 'message',
    'fa-hand-wave': 'users',
    'fa-layer-group': 'package',
    'fa-key': 'key'
  },

  apply() {
    // 1. Reemplazar elementos con data-icon (método nuevo)
    document.querySelectorAll('[data-icon]').forEach(el => {
      const iconName = el.getAttribute('data-icon');
      el.innerHTML = window.getIcon(iconName);
    });

    // 2. Reemplazar clases FontAwesome (para migración automática)
    Object.keys(this.map).forEach(faClass => {
      document.querySelectorAll(`.${faClass}`).forEach(el => {
        const iconName = this.map[faClass];
        const newSvg = document.createElement('span');
        newSvg.innerHTML = window.getIcon(iconName);
        
        // Preservar clases de tamaño o estilo si existen, excepto la de FA
        el.className.split(' ').forEach(cls => {
          if (!cls.startsWith('fa-')) {
            newSvg.className += ` ${cls}`;
          }
        });
        
        el.parentNode.replaceChild(newSvg.firstElementChild, el);
      });
    });
  }
};

document.addEventListener('DOMContentLoaded', () => IconManager.apply());
window.IconManager = IconManager;
