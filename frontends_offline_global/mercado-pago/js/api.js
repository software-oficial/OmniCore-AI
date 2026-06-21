/**
 * 🔌 Capa de Servicio (API) - Mercado Pago
 * Gestiona la comunicación con el servidor o la simulación de datos (Mock).
 */
const PaymentAPI = {
  // Datos simulados para el Modo Offline
  MOCK_DATA: {
    clients: [
      {
        id: 1,
        name: 'Tienda Tech Alpha',
        email: 'contacto@techalpha.com',
        account_status: 'active',
        has_whatsapp_hub: true,
        has_stock_pro: true,
        access_token: 'mock_token_1',
        public_key: 'pub_1',
        client_id: 'cid_1',
      },
      {
        id: 2,
        name: 'Modas Elegantes',
        email: 'ventas@modaselegantes.com',
        account_status: 'active',
        has_whatsapp_hub: true,
        has_stock_pro: false,
        access_token: 'mock_token_2',
        public_key: 'pub_2',
        client_id: 'cid_2',
      },
      {
        id: 3,
        name: 'Suministros Industriales',
        email: 'admin@sumindust.com',
        account_status: 'suspended',
        has_whatsapp_hub: false,
        has_stock_pro: true,
        access_token: 'mock_token_3',
        public_key: 'pub_3',
        client_id: 'cid_3',
      },
      {
        id: 4,
        name: 'Café Gourmet',
        email: 'hola@cafegourmet.com',
        account_status: 'active',
        has_whatsapp_hub: true,
        has_stock_pro: true,
        access_token: 'mock_token_4',
        public_key: 'pub_4',
        client_id: 'cid_4',
      },
    ],
    payments: {
      all: [
        {
          id: 101,
          client_name: 'Tienda Tech Alpha',
          amount: 150.0,
          status: 'approved',
          created_at: '2023-10-20T10:00:00Z',
        },
        {
          id: 102,
          client_name: 'Modas Elegantes',
          amount: 85.5,
          status: 'pending',
          created_at: '2023-10-21T15:30:00Z',
        },
        {
          id: 103,
          client_name: 'Café Gourmet',
          amount: 200.0,
          status: 'approved',
          created_at: '2023-10-22T09:15:00Z',
        },
      ],
      byClient: {
        1: [
          {
            id: 201,
            amount: 45.0,
            status: 'approved',
            created_at: '2023-10-20T11:00:00Z',
            init_point: 'https://mercadopago.com/mock-pay-1',
          },
          {
            id: 202,
            amount: 120.0,
            status: 'pending',
            created_at: '2023-10-21T12:00:00Z',
            init_point: 'https://mercadopago.com/mock-pay-2',
          },
        ],
      },
    },
    subscriptions: {
      1: [
        {
          id: 501,
          plan_id: 'plan_premium_mensual',
          amount: 29.99,
          frequency: 'monthly',
          status: 'active',
          created_at: '2023-09-01T00:00:00Z',
        },
        {
          id: 502,
          plan_id: 'plan_enterprise_anual',
          amount: 299.0,
          frequency: 'yearly',
          status: 'active',
          created_at: '2023-08-15T00:00:00Z',
        },
      ],
    },
    licenseAudit: [
      { feature_id: 'stock.pro_reports' },
      { feature_id: 'whatsapp.bot_core' },
      { feature_id: 'gateway.premium_support' },
    ],
  },

  async fetch(endpoint, method = 'GET', body = null) {
    console.log(`[API] ${method} ${endpoint}`, body);

    if (CONFIG.IS_MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 400));

      if (method === 'GET') {
        if (endpoint === '/clients') {
          return { clients: this.MOCK_DATA.clients };
        }
        if (endpoint === '/payments/all') {
          return { payments: this.MOCK_DATA.payments.all };
        }
        if (endpoint.startsWith('/payments/')) {
          const clientId = endpoint.split('/').pop();
          return { payments: this.MOCK_DATA.payments.byClient[clientId] || [] };
        }
        if (endpoint.startsWith('/subscriptions/')) {
          const clientId = endpoint.split('/').pop();
          return { subscriptions: this.MOCK_DATA.subscriptions[clientId] || [] };
        }
        if (endpoint.startsWith('/api/master/license/audit/')) {
          return { data: this.MOCK_DATA.licenseAudit };
        }
      }
      // Simular éxito para cualquier escritura
      return { success: true, message: 'Operación simulada con éxito' };
    }

    try {
      const headers = { 'Content-Type': 'application/json' };
      const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, {
        method: method,
        headers: headers,
        body: body ? JSON.stringify(body) : null,
      });
      if (!response.ok) {throw new Error(`HTTP error! status: ${response.status}`);}
      return await response.json();
    } catch (e) {
      throw new Error(`Error de conexión: ${e.message}`, { cause: e });
    }
  },
};

window.PaymentAPI = PaymentAPI;
