/**
 * 🎨 Lógica de Interfaz - Stock Pro
 * Gestiona el DOM, eventos y la interacción con el usuario.
 * Utiliza StockAPI para la comunicación de datos.
 */

// Función de utilidad para evitar llamadas excesivas a la API
function debounce(func, wait = 300) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

const app = {
  state: {
    currentView: localStorage.getItem('current_view') || 'view-login',
    token: localStorage.getItem('session_token'),
    user: JSON.parse(localStorage.getItem('user_data') || '{}'),
    role: localStorage.getItem('user_role') || 'empleado',
    isPro: true,
    theme: localStorage.getItem('theme') || CONFIG.THEME_DEFAULT,
    lang: localStorage.getItem('lang') || CONFIG.LANG_DEFAULT,
    cart: [],
    translations: {},
  },

  async init() {
    console.log('🚀 Stock Pro: Iniciando...');
    try {
      await this.loadConfig();
      await this.loadTranslations();
      this.applyTheme();
      this.applyTranslations();
      this.setupDebouncedHandlers();

      if (CONFIG.IS_MOCK_MODE) {
        console.log('🛠️ Modo Simulación activo.');
        this.state.token = StockAPI.MOCK_DATA.session.token;
        this.state.user = StockAPI.MOCK_DATA.session.user;
        this.state.role = StockAPI.MOCK_DATA.session.user.role;
        this.setupAuthenticatedUI();
        this.loadStock();
        this.switchView('view-stock');
        console.log('✅ Forced view-stock for Mock Mode');
      } else {
        if (this.state.token && this.state.user.id) {
          const validation = await StockAPI.call('auth.validate_session', {
            token: this.state.token,
          });
          if (validation && validation.status === 'success') {
            this.setupAuthenticatedUI();
            this.loadStock();
            const targetView =
              this.state.currentView && this.state.currentView !== 'view-login'
                ? this.state.currentView
                : 'view-stock';
            this.switchView(targetView);
          } else {
            this.logout();
          }
        } else {
          this.switchView('view-login');
        }
      }
    } catch (e) {
      console.error('❌ Error crítico:', e);
      Toast.error('Error al cargar la aplicación.');
      this.switchView('view-login');
    }
  },

  setupAuthenticatedUI() {
    if (this.state.role === 'OWNER') {
      const navPersonnel = document.getElementById('nav-personnel');
      if (navPersonnel) {navPersonnel.classList.remove('hidden');}
    }
    this.updateGlobalUI(false);
  },

  updateGlobalUI(isHidden) {
    const nav = document.getElementById('bottom-nav');
    if (!nav) {return;}
    if (isHidden) {
      nav.classList.add('hidden');
      nav.style.display = 'none';
    } else {
      nav.classList.remove('hidden');
      nav.style.display = 'flex';
    }
  },

  switchView(viewId) {
    this.state.currentView = viewId;
    localStorage.setItem('current_view', viewId);
    document.querySelectorAll('.view').forEach((v) => v.classList.remove('active'));
    const view = document.getElementById(viewId);
    if (view) {view.classList.add('active');}
    document.querySelectorAll('.nav-item').forEach((item) => {
      item.classList.toggle('active', item.getAttribute('data-view') === viewId);
    });
    const submenu = document.getElementById('submenu-popup');
    if (submenu) {submenu.classList.remove('active');}

    if (viewId === 'view-personnel') {this.loadPersonnel();}
    if (viewId === 'view-subscription') {this.loadSubscription();}
    if (viewId === 'view-alias') {this.loadAliases();}
    if (viewId === 'view-cash') {this.loadCashStatus();}
    if (viewId === 'view-reports') {this.loadReports();}

    const isAuthView = viewId === 'view-login' || viewId === 'view-register';
    const nav = document.getElementById('bottom-nav');
    if (nav) {
      if (isAuthView) {
        nav.classList.add('hidden');
        nav.style.display = 'none';
      } else {
        nav.classList.remove('hidden');
        nav.style.display = 'flex';
      }
    }
  },

  async login() {
    console.log('👉 login() called');
    const user = document.getElementById('login-user').value;
    const pass = document.getElementById('login-pass').value;

    if (!CONFIG.IS_MOCK_MODE && (!user || !pass)) {
      Toast.warning('Completa datos');
      return;
    }

    const res = await StockAPI.call('auth.login', { username: user, password: pass });
    if (res.status === 'success') {
      this.state.token = res.token;
      this.state.user = res.user;
      this.state.role = res.user.role;
      Toast.success(`¡Bienvenido ${user || 'Admin'}!`);
      this.setupAuthenticatedUI();
      this.loadStock();
      this.switchView('view-stock');
    } else {
      Toast.error(res.message);
    }
  },

  async registerOwner() {
    console.log('👉 registerOwner() called');
    const biz = document.getElementById('reg-business').value;
    const user = document.getElementById('reg-user').value;
    const pass = document.getElementById('reg-pass').value;

    if (!CONFIG.IS_MOCK_MODE && (!biz || !user || !pass)) {
      Toast.warning('Completa datos');
      return;
    }

    const res = await StockAPI.call('auth.register_owner', {
      business_name: biz,
      username: user,
      password: pass,
    });
    if (res.status === 'success') {
      Toast.success('Registrado');
      this.switchView('view-login');
    } else {
      Toast.error(res.message);
    }
  },

  async logout() {
    localStorage.clear();
    this.state.token = null;
    this.state.user = {};
    this.state.role = 'empleado';
    Toast.info('Sesión cerrada');
    this.switchView('view-login');
  },

  togglePassword(inputId) {
    const input = document.getElementById(inputId);
    if (input) {input.type = input.type === 'password' ? 'text' : 'password';}
  },

  async inviteEmployee() {
    const user = document.getElementById('emp-user')?.value.trim();
    const pass = document.getElementById('emp-pass')?.value;
    if (!user || !pass) {
      Toast.warning('Datos incompletos');
      return;
    }
    const res = await StockAPI.call('user.invite_employee', {
      username: user,
      password: pass,
      tenant_id: this.state.user.tenant_id,
    });
    if (res.status === 'success') {
      Toast.success('Empleado agregado');
      this.loadPersonnel();
    } else {
      Toast.error(res.message);
    }
  },

  async loadPersonnel() {
    const res = await StockAPI.call('user.list', { tenant_id: this.state.user.tenant_id });
    const container = document.getElementById('personnel-table-body');
    if (!container) {return;}
    container.innerHTML = '';
    if (res.status === 'success' && res.data) {
      res.data.forEach((u) => {
        const row = document.createElement('tr');
        row.innerHTML = `
                    <td>${u.username}</td>
                    <td><span class="badge badge-success">${u.role}</span></td>
                    <td>
                        <button class="btn btn-secondary" style="padding:4px 8px" onclick="app.promptPermission('${u.id}')">🔑</button>
                        <button class="btn btn-danger" style="padding:4px 8px" onclick="app.revokeAccess('${u.id}')">🗑️</button>
                    </td>
                `;
        container.appendChild(row);
      });
    }
  },

  async promptPermission(userId) {
    const permKey = prompt('Llave del permiso:');
    if (!permKey) {return;}
    const granted = confirm(`¿Conceder ${permKey}?`);
    await StockAPI.call('user.set_permission', {
      user_id: userId,
      permission_key: permKey,
      granted,
    });
    Toast.success('Permiso actualizado');
    this.loadPersonnel();
  },

  async revokeAccess(userId) {
    if (!confirm('¿Revocar acceso?')) {return;}
    const res = await StockAPI.call('user.revoke_access', { user_id: userId });
    if (res.status === 'success') {
      Toast.success('Acceso revocado');
      this.loadPersonnel();
    } else {
      Toast.error(res.message);
    }
  },

  async loadStock() {
    const filter = document.getElementById('stock-search')?.value || '';
    const res = await StockAPI.call('stock.list', { filter });
    const tbody = document.getElementById('stock-table-body');
    if (!tbody) {return;}
    tbody.innerHTML = '';
    if (res.status === 'success' && res.data) {
      res.data.forEach((p) => {
        const row = document.createElement('tr');
        row.innerHTML = `
                    <td>${p.codigo || '-'}</td>
                    <td>${p.nombre || '-'}</td>
                    <td>${p.categoria || '-'}</td>
                    <td>$${parseFloat(p.precio || 0).toFixed(2)}</td>
                    <td>${p.cantidad || 0}</td>
                    <td>
                        <button class="btn btn-secondary" style="padding:4px 8px" onclick="app.editProduct('${p.codigo}')">✏️</button>
                        <button class="btn btn-danger" style="padding:4px 8px" onclick="app.deleteProduct('${p.codigo}')">🗑️</button>
                    </td>
                `;
        tbody.appendChild(row);
      });
    }
  },

  setupDebouncedHandlers() {
    this.debouncedLoadStock = debounce(() => this.loadStock());
    this.debouncedQuickAdd = debounce(() => this.quickAddProduct());
  },

  showModal(id) {
    const modal = document.getElementById(id);
    if (modal) {modal.classList.remove('hidden');}
  },

  closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {modal.classList.add('hidden');}
  },

  async saveProduct() {
    const params = {
      codigo: document.getElementById('p-code')?.value,
      nombre: document.getElementById('p-name')?.value,
      precio: parseFloat(document.getElementById('p-price')?.value || 0),
      cantidad: parseFloat(document.getElementById('p-qty')?.value || 0),
      categoria: document.getElementById('p-cat')?.value,
      es_peso: document.getElementById('p-weight')?.checked || false,
    };
    const res = await StockAPI.call('stock.add', params);
    if (res.status === 'success') {
      Toast.success('Producto guardado');
      this.closeModal('modal-product');
      this.loadStock();
    } else {
      Toast.error(res.message);
    }
  },

  async editProduct(codigo) {
    const res = await StockAPI.call('stock.get', { codigo });
    if (res.status === 'success') {
      const p = res.data;
      document.getElementById('p-code').value = p.codigo;
      document.getElementById('p-name').value = p.nombre;
      document.getElementById('p-price').value = p.precio;
      document.getElementById('p-qty').value = p.cantidad;
      document.getElementById('p-cat').value = p.categoria;
      document.getElementById('p-weight').checked = p.es_peso;
      this.showModal('modal-product');
    }
  },

  async deleteProduct(codigo) {
    if (confirm('¿Eliminar producto?')) {
      const res = await StockAPI.call('stock.delete', { codigo });
      if (res.status === 'success') {
        Toast.success('Producto eliminado');
        this.loadStock();
      } else {
        Toast.error(res.message);
      }
    }
  },

  async quickAddProduct() {
    const codigo = document.getElementById('sale-scan')?.value;
    if (!codigo || codigo.length < 2) {return;}
    const res = await StockAPI.call('venta.add', { codigo });
    if (res.status === 'success') {
      this.state.cart.push(res.data);
      this.renderCart();
      document.getElementById('sale-scan').value = '';
      Toast.success('Producto agregado');
    } else {
      Toast.error(res.message);
    }
  },

  renderCart() {
    const container = document.getElementById('cart-items');
    if (!container) {return;}
    container.innerHTML = '';
    let total = 0;
    this.state.cart.forEach((item, idx) => {
      const subtotal = (item.precio || 0) * (item.cantidad || 1);
      total += subtotal;
      const div = document.createElement('div');
      div.style.cssText =
        'display:flex; justify-content:space-between; margin-bottom:8px; padding:8px; background:var(--background); border-radius:8px; font-size:0.9rem;';
      div.innerHTML = `
                <span>${item.nombre} x ${item.cantidad || 1}</span>
                <span>$${subtotal.toFixed(2)} <button onclick="app.removeFromCart(${idx})" style="border:none; background:none; cursor:pointer; color:var(--error)">🗑️</button></span>
            `;
      container.appendChild(div);
    });
    const totalEl = document.getElementById('cart-total');
    if (totalEl) {totalEl.innerText = `$${total.toFixed(2)}`;}
  },

  removeFromCart(idx) {
    this.state.cart.splice(idx, 1);
    this.renderCart();
    Toast.info('Removido');
  },

  openCheckout() {
    if (this.state.cart.length === 0) {
      Toast.warning('Carrito vacío');
      return;
    }
    this.showModal('modal-checkout');
  },

  async confirmSale() {
    const res = await StockAPI.call('venta.cobrar', { items: this.state.cart });
    if (res.status === 'success') {
      Toast.success('Venta registrada');
      this.state.cart = [];
      this.renderCart();
      this.closeModal('modal-checkout');
    } else {
      Toast.error(res.message);
    }
  },

  async loadSubscription() {
    const container = document.getElementById('current-plan');
    if (container && this.state.user) {
      container.innerHTML = `
                <strong>Plan:</strong> ${this.state.user.plan}<br>
                <strong>Créditos:</strong> ${this.state.user.credits}<br>
                <strong>Tenant:</strong> ${this.state.user.tenant_id}
            `;
    }
  },

  async loadAliases() {
    const res = await StockAPI.call('alias.list', {});
    const container = document.getElementById('alias-table-body');
    if (!container) {return;}
    container.innerHTML = '';
    if (res.status === 'success' && res.data) {
      res.data.forEach((a) => {
        const row = document.createElement('tr');
        row.innerHTML = `
                    <td>${a.nombre}</td>
                    <td>$${parseFloat(a.limite || 0).toFixed(2)}</td>
                    <td>$${parseFloat(a.acumulado || 0).toFixed(2)}</td>
                    <td>
                        <button class="btn btn-danger" style="padding:4px 8px" onclick="app.deleteAlias('${a.id}')">🗑️</button>
                    </td>
                `;
        container.appendChild(row);
      });
    }
  },

  async loadCashStatus() {
    const res = await StockAPI.call('caja.status', {});
    const container = document.getElementById('cash-status');
    if (!container) {return;}
    if (res.status === 'success' && res.data) {
      const laD = res.data;
      const total = (laD.ventas_efectivo || 0) + (laD.ventas_digital || 0);
      container.innerHTML = `
                <strong>Estado:</strong> ${laD.id ? '🟢 Abierta' : '🔴 Cerrada'}<br>
                <strong>Ventas Efectivo:</strong> $${parseFloat(laD.ventas_efectivo || 0).toFixed(2)}<br>
                <strong>Ventas Digital:</strong> $${parseFloat(laD.ventas_digital || 0).toFixed(2)}<br>
                <strong>Total Esperado:</strong> $${total.toFixed(2)}
            `;
    } else {
      container.innerHTML = 'Caja cerrada.';
    }
  },

  async loadReports() {
    const [resS, resA] = await Promise.all([
      StockAPI.call('reporte.resumen', {}),
      StockAPI.call('reporte.alertas', {}),
    ]);
    const summaryEl = document.getElementById('report-summary');
    if (summaryEl && resS.status === 'success') {
      const d = resS.data;
      summaryEl.innerHTML = `<strong>Total:</strong> $${parseFloat(d.total_facturado).toFixed(2)}<br><strong>Ganancia:</strong> $${parseFloat(d.ganancia_estimada).toFixed(2)}`;
    }
    const alertsEl = document.getElementById('report-alerts');
    if (alertsEl && resA.status === 'success') {
      alertsEl.innerHTML = resA.data
        .map(
          (p) => `
                <div style="padding:10px; margin-bottom:10px; background:rgba(239, 68, 68, 0.1); border-left: 4px solid var(--error); border-radius:4px; font-size:0.9rem;">
                    <strong>${p.nombre}</strong>: Solo quedan ${p.cantidad} unidades.
                </div>
            `
        )
        .join('');
    }
  },

  async deleteAlias(id) {
    if (confirm('¿Eliminar?')) {
      await StockAPI.call('alias.delete', { alias_id: id });
      Toast.success('Eliminado');
      this.loadAliases();
    }
  },

  async openCash() {
    await StockAPI.call('caja.abrir', {});
    Toast.success('Caja abierta');
    this.loadCashStatus();
  },

  async closeCash() {
    await StockAPI.call('caja.cerrar', {});
    Toast.success('Caja cerrada');
    this.loadCashStatus();
  },

  async loadConfig() {
    return true;
  },
  async loadTranslations() {
    this.state.translations = {};
    return true;
  },
  applyTheme() {
    console.log('Theme applied:', this.state.theme);
  },
  applyTranslations() {
    console.log('Translations applied');
  },
  setTheme(t) {
    this.state.theme = t;
    localStorage.setItem('theme', t);
    Toast.info('Tema cambiado');
  },
  setLang(l) {
    this.state.lang = l;
    localStorage.setItem('lang', l);
    Toast.info('Idioma cambiado');
  },
  exportCSV() {
    Toast.success('CSV Exportado (Mock)');
  },
};

document.addEventListener('DOMContentLoaded', () => {
  app.init();
});

window.app = app; // Make app globally accessible
