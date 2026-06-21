/**
 * 🔌 Capa de Servicio (API) - WhatsApp
 * Versión Autónoma (Mock Mode)
 */
const WhatsAppAPI = {
  MOCK_DATA: {
    conversations: [
      { phone_number: '5491122334455', name: 'Juan Pérez', is_human_intervening: false },
      { phone_number: '5491166778899', name: 'María García', is_human_intervening: true },
      { phone_number: '5491100112233', name: 'Carlos Tech', is_human_intervening: false },
    ],
    messages: {
      '5491122334455': [
        { sender: 'client', content: 'Hola, quiero saber más.', timestamp: new Date().toISOString() },
        { sender: 'bot', content: '¡Hola! ¿En qué te ayudo?', timestamp: new Date().toISOString() },
      ],
      '5491166778899': [
        { sender: 'client', content: 'Pedido retrasado', timestamp: new Date().toISOString() },
      ]
    },
    bots: [
      { id: 'bot_1', name: 'Bot Ventas', active: true, type: 'AI-Flow', last_sync: 'Ahora' },
      { id: 'bot_2', name: 'Bot Soporte', active: false, type: 'Keyword', last_sync: '1h' },
    ],
    welcome_config: { enabled: true, message: 'Hola!', delay: 1000 },
    tokens: [
      { name: 'Producción', value: 'WAPP_PROD_123' },
      { name: 'Testeo', value: 'WAPP_TEST_456' },
    ],
    webhooks: [
      { url: 'https://webhook.site/123', status: 'Active' },
    ],
  },

  async fetchConversations() { return this.MOCK_DATA.conversations; },
  async fetchMessages(phone) { return this.MOCK_DATA.messages[phone] || []; },
  async sendMessage(phone, content) {
    if (!this.MOCK_DATA.messages[phone]) this.MOCK_DATA.messages[phone] = [];
    this.MOCK_DATA.messages[phone].push({ sender: 'human', content, timestamp: new Date().toISOString() });
    return { status: 'success' };
  },
  async deleteConversation(phone) { return { status: 'success' }; },
  async toggleIntervention(phone, status) { return { status: 'success' }; },
  async fetchBots() { return this.MOCK_DATA.bots; },
  async fetchWelcomeConfig() { return this.MOCK_DATA.welcome_config; },
  async updateWelcomeConfig(data) { return { status: 'success' }; },
  async fetchTokens() { return this.MOCK_DATA.tokens; },
  async fetchWebhooks() { return this.MOCK_DATA.webhooks; },
  async updateToken(name, value) { return { status: 'success' }; },
  async updateWebhook(url) { return { status: 'success' }; }
};

window.WhatsAppAPI = WhatsAppAPI;
