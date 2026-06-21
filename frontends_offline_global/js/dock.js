/**
 * 🍏 Mac Dock & Advanced Menu Controller
 * Maneja la interactividad de la navegación inferior y el menú de configuración.
 */

const DockController = {
  /**
   * Configuraciones específicas por módulo
   */
  moduleConfigs: {
    '/mercado-pago/': [
      { label: 'Clientes', icon: 'users', action: "showSection('clients')" },
      { label: 'Cobros', icon: 'credit_card', action: "showSection('payments')" },
      { label: 'Global', icon: 'chart', action: "showSection('global_payments')" },
      { label: 'Suscrip.', icon: 'key', action: "showSection('subscriptions')" }
    ],
    '/stock/': [
      { label: 'Inventario', icon: 'package', action: "app.switchView('view-stock')" },
      { label: 'Caja', icon: 'cash', action: "app.switchView('view-cash')" },
      { label: 'Reportes', icon: 'chart', action: "app.switchView('view-reports')" },
      { label: 'Staff', icon: 'users', action: "app.switchView('view-personnel')" }
    ],
    '/whatsapp/': [
      { label: 'Chats', icon: 'message', action: "showView('view-chats')" },
      { label: 'Bots', icon: 'bot', action: "showView('view-bots')" },
      { label: 'Flujos', icon: 'package', action: "showView('view-flows')" },
      { label: 'Config.', icon: 'edit', action: "showView('view-config')" }
    ]
  },

  getDockConfig() {
    const path = window.location.pathname;
    for (const [module, config] of Object.entries(this.moduleConfigs)) {
      if (path.includes(module)) return config;
    }
    return []; // Default si no coincide
  },

  /**
   * Genera el HTML del dock dinámicamente
   */
  renderDock() {
    console.log('DockController: Iniciando renderizado');
    const config = this.getDockConfig();
    if (config.length === 0) return;

    const container = document.createElement('div');
    container.className = 'mac-dock-container';
    
    const dock = document.createElement('div');
    dock.className = 'mac-dock';
    
    config.forEach(item => {
      const dockItem = document.createElement('div');
      dockItem.className = 'dock-item';
      dockItem.setAttribute('data-label', item.label);
      
      const iconHtml = window.getIcon ? window.getIcon(item.icon) : '';
      dockItem.innerHTML = iconHtml || '•';
      
      if (item.action) {
        dockItem.setAttribute('onclick', item.action);
      }
      
      dock.appendChild(dockItem);
    });
    
    container.appendChild(dock);
    document.body.appendChild(container);
    console.log('DockController: Dock añadido al DOM');
  },

  /**
   * Alterna la visibilidad del menú avanzado (bottom sheet)
   */
  toggleAdvancedMenu() {
    const menu = document.getElementById('advanced-menu');
    if (!menu) {
      this.renderAdvancedMenu();
      return this.toggleAdvancedMenu();
    }
    
    const sheet = menu.querySelector('.advanced-menu-sheet');
    
    if (menu.classList.contains('hidden')) {
      menu.classList.remove('hidden');
      setTimeout(() => sheet.classList.add('open'), 10);
    } else {
      sheet.classList.remove('open');
      setTimeout(() => menu.classList.add('hidden'), 400);
    }
  },

  /**
   * Renderiza el menú avanzado si no existe
   */
  renderAdvancedMenu() {
    const menuHtml = `
      <div id="advanced-menu" class="advanced-menu-overlay hidden" onclick="if(event.target === this) toggleAdvancedMenu()">
        <div class="advanced-menu-sheet">
          <div class="menu-handle" onclick="toggleAdvancedMenu()"></div>
          <h3 class="mb-4 font-bold text-lg">Configuración Global</h3>
          <div class="menu-item" onclick="alert('Perfil')">
            <i>👤</i>
            <span>Mi Perfil</span>
          </div>
          <div class="menu-item" onclick="alert('Notificaciones')">
            <i>🔔</i>
            <span>Notificaciones</span>
          </div>
          <div class="menu-item" onclick="alert('Apariencia')">
            <i>🌓</i>
            <span>Tema (Auto/Light/Dark)</span>
          </div>
          <div class="pt-4 mt-4 border-t border-slate-100">
            <div class="menu-item text-red-500" onclick="alert('Salir')">
              <i>🚪</i>
              <span>Cerrar Sesión</span>
            </div>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', menuHtml);
  },

  /**
   * Inicializa el dock
   */
  init() {
    console.log('DockController: init() llamado');
    // Si ya hay un dock, no hacer nada
    if (document.querySelector('.mac-dock-container')) {
        console.log('DockController: Dock ya existe en el DOM');
        return;
    }
    
    // Esperar a que icons.js se cargue si es necesario
    if (window.getIcon) {
      console.log('DockController: getIcon disponible, renderizando');
      this.renderDock();
    } else {
      console.log('DockController: getIcon NO disponible, esperando evento');
      document.addEventListener('iconsLoaded', () => {
        console.log('DockController: iconsLoaded evento recibido');
        this.renderDock()
      });
    }
  }
};

// Exportar funciones al objeto window para acceso directo desde el HTML
window.toggleAdvancedMenu = () => DockController.toggleAdvancedMenu();
window.DockController = DockController;

// Autoejecutar init al cargar el DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log('DockController: DOMContentLoaded');
    DockController.init();
  });
} else {
  console.log('DockController: DOM ya cargado, ejecutando init');
  DockController.init();
}
