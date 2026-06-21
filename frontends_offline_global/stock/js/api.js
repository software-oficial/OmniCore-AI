/**
 * 🔌 Capa de Servicio (API) - Stock Pro
 * Gestiona los comandos del sistema y la simulación de datos (Mock).
 */
const StockAPI = {
  MOCK_DATA: {
    session: {
      token: 'mock_token_stock_123',
      user: {
        id: 'user_admin_01',
        username: 'admin_stock',
        role: 'OWNER',
        tenant_id: 'tenant_demo_01',
        plan: 'PRO',
        credits: 500,
      },
    },
    products: [
      {
        codigo: 'PROD001',
        nombre: 'Laptop Gamer X',
        precio: 1200.0,
        cantidad: 5,
        categoria: 'Electrónica',
        es_peso: false,
      },
      {
        codigo: 'PROD002',
        nombre: 'Mouse Óptico RGB',
        precio: 25.5,
        cantidad: 50,
        categoria: 'Accesorios',
        es_peso: false,
      },
      {
        codigo: 'PROD003',
        nombre: 'Teclado Mecánico',
        precio: 80.0,
        cantidad: 15,
        categoria: 'Accesorios',
        es_peso: false,
      },
      {
        codigo: 'PROD004',
        nombre: 'Café en Grano (1kg)',
        precio: 15.0,
        cantidad: 100,
        categoria: 'Alimentos',
        es_peso: true,
      },
      {
        codigo: 'PROD005',
        nombre: 'Monitor 27" 4K',
        precio: 350.0,
        cantidad: 3,
        categoria: 'Electrónica',
        es_peso: false,
      },
    ],
    personnel: [
      { id: 'u1', username: 'admin_stock', role: 'OWNER' },
      { id: 'u2', username: 'empleado_juan', role: 'empleado' },
      { id: 'u3', username: 'empleado_ana', role: 'empleado' },
    ],
    aliases: [
      { id: 'a1', nombre: 'Cliente Fiel 1', limite: 1000.0, acumulado: 250.0 },
      { id: 'a2', nombre: 'Empresa Tech', limite: 5000.0, acumulado: 1200.0 },
    ],
    cash: {
      id: 'cash_active_01',
      ventas_efectivo: 450.75,
      ventas_digital: 210.2,
    },
    reports: {
      total_facturado: 8500.4,
      ganancia_estimada: 2550.12,
    },
    alerts: [
      { nombre: 'Monitor 27" 4K', cantidad: 3 },
      { nombre: 'Laptop Gamer X', cantidad: 5 },
    ],
  },

  async call(command, params = {}) {
    if (CONFIG.IS_MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300));
      console.log(`[MOCK API] Comando: ${command}`, params);

      switch (command) {
        case 'auth.login':
          return { status: 'success', token: 'mock_token', user: this.MOCK_DATA.session.user };
        case 'auth.register_owner':
          return { status: 'success' };
        case 'auth.validate_session':
          return { status: 'success' };
        case 'stock.list': {
          const filter = params.filter || '';
          const filtered = this.MOCK_DATA.products.filter(
            (p) =>
              p.nombre.toLowerCase().includes(filter.toLowerCase()) ||
              p.codigo.toLowerCase().includes(filter.toLowerCase())
          );
          return { status: 'success', data: filtered };
        }
        case 'stock.get': {
          const p = this.MOCK_DATA.products.find((x) => x.codigo === params.codigo);
          return p ? { status: 'success', data: p } : { status: 'error', message: 'No encontrado' };
        }
        case 'stock.add': {
          this.MOCK_DATA.products.push({ ...params, codigo: params.codigo || 'NEW' + Date.now() });
          return { status: 'success' };
        }
        case 'stock.delete': {
          this.MOCK_DATA.products = this.MOCK_DATA.products.filter(
            (x) => x.codigo !== params.codigo
          );
          return { status: 'success' };
        }
        case 'user.list':
          return { status: 'success', data: this.MOCK_DATA.personnel };
        case 'user.invite_employee': {
          this.MOCK_DATA.personnel.push({
            id: 'u' + Date.now(),
            username: params.username,
            role: 'empleado',
          });
          return { status: 'success' };
        }
        case 'user.revoke_access': {
          this.MOCK_DATA.personnel = this.MOCK_DATA.personnel.filter(
            (x) => x.id !== params.user_id
          );
          return { status: 'success' };
        }
        case 'venta.add': {
          const prod = this.MOCK_DATA.products.find((x) => x.codigo === params.codigo);
          return prod
            ? { status: 'success', data: prod }
            : { status: 'error', message: 'Producto no encontrado' };
        }
        case 'venta.cobrar': {
          return { status: 'success' };
        }
        case 'alias.list': {
          return { status: 'success', data: this.MOCK_DATA.aliases };
        }
        case 'alias.delete': {
          this.MOCK_DATA.aliases = this.MOCK_DATA.aliases.filter((x) => x.id !== params.alias_id);
          return { status: 'success' };
        }
        case 'caja.status': {
          return { status: 'success', data: this.MOCK_DATA.cash };
        }
        case 'caja.abrir': {
          this.MOCK_DATA.cash.id = 'cash_active_' + Date.now();
          return { status: 'success' };
        }
        case 'caja.cerrar': {
          this.MOCK_DATA.cash.id = null;
          return { status: 'success' };
        }
        case 'reporte.resumen': {
          return { status: 'success', data: this.MOCK_DATA.reports };
        }
        case 'reporte.alertas': {
          return { status: 'success', data: this.MOCK_DATA.alerts };
        }
        case 'sys.subscription.update': {
          return { status: 'success' };
        }
        default:
          return { status: 'error', message: 'Comando no implementado en Mock' };
      }
    }

    try {
      const headers = { 'Content-Type': 'application/json' };
      // El token se maneja en el estado de la app, pero el servicio puede requerir un método para setearlo
      const response = await fetch(`${CONFIG.API_BASE}/`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ command, params }),
      });
      const res = await response.json();
      return res.payload || res;
    } catch (e) {
      return { status: 'error', message: `Error de conexión: ${e.message}` };
    }
  },
};

window.StockAPI = StockAPI;
