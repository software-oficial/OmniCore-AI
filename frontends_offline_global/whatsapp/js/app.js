/**
 * 🚀 WhatsApp Hub - Core Logic (SISTEMA REDISEÑADO DESDE CERO)
 * Este archivo ha sido reescrito para eliminar cualquier complejidad innecesaria
 * y garantizar que la navegación sea 100% funcional.
 */

console.log('🔴 [WA HUB] Iniciando carga del sistema...');

// --- Lógica del Constructor de Flujos ---
let flowState = [];

window.addOption = function() {
    flowState.push({ id: Date.now(), label: '', actionType: 'action', children: [] });
    renderFlowBuilder();
};

window.renderFlowBuilder = function() {
    const container = document.getElementById('flow-options');
    if (!container) return;
    container.innerHTML = flowState.map((option, index) => `
        <div class="p-4 border rounded-lg bg-slate-50 space-y-2">
            <input type="text" placeholder="Etiqueta de opción" value="${option.label}" 
                   onchange="flowState[${index}].label = this.value" class="w-full p-2 border rounded" />
            
            <select onchange="flowState[${index}].actionType = this.value; renderFlowBuilder();" class="w-full p-2 border rounded">
                <option value="action" ${option.actionType === 'action' ? 'selected' : ''}>Acción Final</option>
                <option value="submenu" ${option.actionType === 'submenu' ? 'selected' : ''}>Sub-menú</option>
            </select>
            
            ${option.actionType === 'submenu' ? `
                <div class="pl-4 border-l-2 border-blue-200">
                    <p class="text-xs font-bold text-slate-500 mb-2">Sub-opciones:</p>
                    <button class="text-xs text-blue-600">+ Añadir sub-opción</button>
                </div>
            ` : ''}
        </div>
    `).join('');
};

window.saveFlow = function() {
    console.log('Guardando flujo:', JSON.stringify(flowState));
    alert('Flujo guardado en consola.');
};

// 1. CONFIGURACIÓN DE VISTAS
const VIEWS_CONFIG = {
  'view-chats': { title: 'Gestión de Chats', render: null },
  'view-bots': { title: 'Gestión de Bots', render: renderBots },
  'view-flows': { title: 'Gestión de Flujos', render: renderFlowBuilder },
  'view-config': { title: 'Configuración', render: async () => { await renderTokens(); await renderWebhooks(); } },
  'view-bot-config': { title: 'Configuración de Bot', render: null }
};

// 2. FUNCIONES DE RENDERIZADO (Independientes y Seguras)
async function renderBots() {
  console.log('Rendering: Bots...');
  const grid = document.getElementById('bots-grid');
  if (!grid) {return;}
  try {
    const bots = await WhatsAppAPI.fetchBots();
    grid.innerHTML = bots
      .map(
        (bot) => `
            <div class="bg-white p-6 rounded-2xl shadow-sm border flex flex-col justify-between">
                <div>
                    <div class="flex justify-between items-start mb-4">
                        <h4 class="font-bold text-lg">${bot.name}</h4>
                        <span class="px-2 py-1 rounded-full text-[10px] font-bold ${bot.active ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}">
                            ${bot.active ? 'ACTIVO' : 'INACTIVO'}
                        </span>
                    </div>
                    <p class="text-sm text-slate-500 mb-2">Tipo: ${bot.type}</p>
                    <p class="text-xs text-slate-400">Sincronización: ${bot.last_sync}</p>
                </div>
                <div class="mt-6 flex space-x-2">
                    <button onclick="window.configureBot('${bot.name}')" class="flex-1 bg-slate-100 text-slate-600 py-2 rounded-lg text-xs font-bold hover:bg-slate-200 transition-all">Configurar</button>
                    <button onclick="alert('Cambiando estado...')" class="flex-1 ${bot.active ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'} py-2 rounded-lg text-xs font-bold hover:opacity-80 transition-all">
                        ${bot.active ? 'Desactivar' : 'Activar'}
                    </button>
                </div>
            </div>
        `
      )
      .join('');
  } catch (_e) {
    grid.innerHTML = `<p class="text-red-500">Error: ${_e.message}</p>`;
  }
}

async function renderWelcomeConfig() {
  console.log('Rendering: Welcome...');
  try {
    const config = await WhatsAppAPI.fetchWelcomeConfig();
    const enabledEl = document.getElementById('welcome-enabled');
    const textEl = document.getElementById('welcome-text');
    const delayEl = document.getElementById('welcome-delay');
    if (enabledEl) {enabledEl.checked = config.enabled;}
    if (textEl) {textEl.value = config.message;}
    if (delayEl) {delayEl.value = config.delay;}
  } catch (e) {
    console.error('Error Welcome:', e);
  }
}

async function renderVariants() {
  console.log('Rendering: Variants...');
  const body = document.getElementById('variants-table-body');
  if (!body) {return;}
  try {
    const variants = await WhatsAppAPI.fetchVariants();
    body.innerHTML = variants
      .map(
        (v) => `
            <tr class="border-b border-slate-100 hover:bg-slate-50 transition-all">
                <td class="p-4 text-sm font-medium">${v.name}</td>
                <td class="p-4 text-sm text-slate-600">${v.priority}</td>
                <td class="p-4 text-sm text-slate-600">${v.response_time}</td>
            </tr>
        `
      )
      .join('');
  } catch (e) {
    body.innerHTML = '<tr><td colspan="3" class="p-4 text-red-500">Error al cargar</td></tr>';
  }
}

async function renderTokens() {
  console.log('Rendering: Tokens...');
  const grid = document.getElementById('tokens-grid');
  if (!grid) {return;}
  try {
    const tokens = await WhatsAppAPI.fetchTokens();
    grid.innerHTML = tokens
      .map(
        (t) => `
            <div class="bg-white p-6 rounded-2xl shadow-sm border">
                <div class="flex justify-between items-center mb-4">
                    <h4 class="font-bold">${t.name}</h4>
                </div>
                <input type="text" id="token-${t.name}" value="${t.value}" class="w-full bg-slate-50 p-3 rounded-lg font-mono text-sm border mb-4" />
                <button onclick="saveToken('${t.name}', document.getElementById('token-${t.name}').value)" class="w-full bg-green-600 text-white py-2 rounded-lg text-xs font-bold hover:bg-green-700">Guardar Token</button>
            </div>
        `
      )
      .join('');
  } catch (e) {
    grid.innerHTML = '<p class="text-red-500">Error al cargar tokens</p>';
  }
}

async function renderWebhooks() {
  console.log('Rendering: Webhooks...');
  const list = document.getElementById('webhooks-list');
  if (!list) {return;}
  try {
    const webhooks = await WhatsAppAPI.fetchWebhooks();
    list.innerHTML = webhooks
      .map(
        (w, index) => `
            <div class="bg-white p-4 rounded-2xl shadow-sm border space-y-2">
                <input type="text" id="webhook-${index}" value="${w.url}" class="w-full p-2 border rounded-lg text-sm" />
                <button onclick="saveWebhook(document.getElementById('webhook-${index}').value)" class="bg-slate-800 text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-black">Guardar Webhook</button>
            </div>
        `
      )
      .join('');
  } catch (e) {
    list.innerHTML = '<p class="text-red-500">Error al cargar webhooks</p>';
  }
}

// Exponer las funciones al objeto window para seguridad
window.showView = switchView;
window.renderBots = renderBots;
window.renderTokens = renderTokens;
window.renderWebhooks = renderWebhooks;

// 3. MOTOR DE NAVEGACIÓN (Consolidado)
async function switchView(viewId) {
  console.log('👉 Solicitud de cambio a:', viewId);

  // A. Ocultar todas las vistas
  document.querySelectorAll('.view-container').forEach((v) => {
    v.classList.add('hidden');
  });

  // B. Mostrar la vista seleccionada
  const target = document.getElementById(viewId);
  if (!target) {
    console.error('❌ Error: No existe la vista', viewId);
    return;
  }
  target.classList.remove('hidden');

  // C. Actualizar Título
  const titleEl = document.getElementById('main-title');
  if (titleEl) {
    titleEl.textContent = VIEWS_CONFIG[viewId]?.title || 'Panel';
  }

  // D. Ejecutar Renderizado si existe
  const renderFn = VIEWS_CONFIG[viewId]?.render;
  if (renderFn) {
    try {
      await renderFn();
    } catch (e) {
      console.error('Error renderizando vista:', viewId, e);
    }
  }
  console.log('✅ Cambio de vista completado.');
}
window.showView = switchView;

// --- Nuevas funciones de Edición ---
window.saveToken = async function(tokenName, newValue) {
    console.log(`Guardando token ${tokenName}:`, newValue);
    try {
        await WhatsAppAPI.updateToken(tokenName, newValue);
        alert(`Token ${tokenName} guardado correctamente.`);
    } catch (e) {
        alert(`Error al guardar token: ${e.message}`);
    }
};

window.saveWebhook = async function(webhookUrl) {
    console.log(`Guardando webhook:`, webhookUrl);
    try {
        await WhatsAppAPI.updateWebhook(webhookUrl);
        alert(`Webhook guardado correctamente: ${webhookUrl}`);
    } catch (e) {
        alert(`Error al guardar webhook: ${e.message}`);
    }
};

window.configureBot = function(botName) {
    console.log(`Configurando bot: ${botName}`);
    
    // 1. Ocultar vistas principales
    document.querySelectorAll('.view-container').forEach(v => v.classList.add('hidden'));
    
    // 2. Crear o limpiar contenedor
    let botConfigView = document.getElementById('view-bot-config');
    if (!botConfigView) {
        botConfigView = document.createElement('div');
        botConfigView.id = 'view-bot-config';
        botConfigView.className = 'view-container';
        document.querySelector('.app-content').appendChild(botConfigView);
    }
    botConfigView.innerHTML = ''; // Limpiar contenido anterior
    
    botConfigView.classList.remove('hidden');
    
    // 3. Renderizar nuevo contenido
    botConfigView.innerHTML = `
        <h3 class="text-lg font-bold mb-6">Configurando: ${botName}</h3>
        <div class="bg-white p-6 rounded-2xl shadow-sm border space-y-4">
            <label class="block text-sm font-bold">Mensaje de respuesta:</label>
            <textarea class="w-full p-2 border rounded-lg" rows="4">Hola, soy ${botName}...</textarea>
            <button onclick="alert('Bot guardado')" class="bg-green-600 text-white px-4 py-2 rounded-lg">Guardar Configuración del Bot</button>
            <button onclick="showView('view-bots')" class="bg-slate-200 px-4 py-2 rounded-lg">Volver</button>
        </div>
    `;
    
    // Actualizar título
    const titleEl = document.getElementById('main-title');
    if (titleEl) titleEl.textContent = 'Configurando Bot';
};

// 4. INICIALIZACIÓN PRINCIPAL
document.addEventListener('DOMContentLoaded', () => {
  console.log('🏁 DOM Listo. Configurando WhatsApp Hub...');

  // --- Lógica de Chats (Simplificada) ---
  const chatListElement = document.getElementById('chat-list');
  const chatViewElement = document.getElementById('chat-view');
  const welcomeViewElement = document.getElementById('welcome-view');
  // Eliminamos referencias a sidebar y nav-link antiguas
  const botSelector = document.getElementById('bot-selector-main');

  let currentPhone = null;

  function showChatView() {
    welcomeViewElement.classList.add('hidden');
    chatViewElement.classList.remove('hidden');
  }
  if (botSelector)
    {botSelector.addEventListener('change', () => {
      showSidebar();
      fetchConversations();
    });}

  async function fetchConversations() {
    try {
      const convs = await WhatsAppAPI.fetchConversations();
      if (!chatListElement) {return;}
      chatListElement.innerHTML = '';
      convs.forEach((chat) => {
        const li = document.createElement('li');
        li.dataset.phone = chat.phone_number;
        li.dataset.name = chat.name || 'Desconocido';
        li.dataset.isHuman = chat.is_human_intervening;
        li.innerHTML = `
                    <div class="chat-item-name"><span>${li.dataset.name}</span><span>${chat.is_human_intervening ? '👤' : '🤖'}</span></div>
                    <div class="chat-item-phone">${chat.phone_number}</div>
                `;
        li.onclick = () =>
          loadChatDetail(chat.phone_number, li.dataset.name, chat.is_human_intervening);
        chatListElement.appendChild(li);
      });
    } catch (e) {
      console.error('Error Chats:', e);
    }
  }

  async function loadChatDetail(phone, name, isHuman) {
    document
      .querySelectorAll('#chat-list li')
      .forEach((li) => li.classList.toggle('selected', li.dataset.phone === phone));
    document.getElementById('chat-header-name').textContent = name;
    document.getElementById('chat-header-phone').textContent = phone;
    showChatView();

    const btn = document.getElementById('human-toggle');
    if (btn) {
      btn.textContent = isHuman ? '👤 Modo Humano (ON)' : '🤖 Modo Bot (ON)';
      btn.className = isHuman ? 'active' : '';
      btn.onclick = () => toggleHuman(phone, isHuman);
    }

    document.getElementById('messages-container').innerHTML = 'Cargando...';
    await fetchMessages(phone);

    document.getElementById('send-message-btn').onclick = () => sendMessage(phone);
    document.getElementById('message-input-text').onkeypress = (_e) => {
      if (_e.key === 'Enter') {sendMessage(phone);}
    };
    document.getElementById('delete-chat-btn').onclick = () => deleteConversation(phone);
  }

  async function fetchMessages(phone) {
    try {
      const msgs = await WhatsAppAPI.fetchMessages(phone);
      const container = document.getElementById('messages-container');
      if (!container) {return;}
      container.innerHTML = msgs
        .map(
          (m) => `
                <div class="message ${m.sender === 'client' ? 'received' : 'sent'}">
                    ${m.sender === 'bot' ? '<span class="msg-sender-label">🤖 Bot</span>' : m.sender === 'human' ? '<span class="msg-sender-label">👤 Tú</span>' : ''}
                    ${m.content}
                    <span class="msg-meta">${new Date(m.timestamp).toLocaleTimeString()}</span>
                </div>
            `
        )
        .join('');
      container.scrollTop = container.scrollHeight;
    } catch (e) {
      console.error('Error Msgs:', e);
    }
  }

  async function sendMessage(phone) {
    const input = document.getElementById('message-input-text');
    const text = input.value.trim();
    if (!text) {return;}
    input.value = '';
    try {
      await WhatsAppAPI.sendMessage(phone, text);
      await fetchMessages(phone);
    } catch (e) {
      alert('Error al enviar');
    }
  }

  async function toggleHuman(phone, status) {
    try {
      await WhatsAppAPI.toggleIntervention(phone, !status);
      alert('Estado cambiado');
      fetchConversations();
    } catch (e) {
      alert('Error');
    }
  }

  async function deleteConversation(phone) {
    if (!confirm('¿Borrar chat?')) {return;}
    try {
      await WhatsAppAPI.deleteConversation(phone);
      showSidebar();
      fetchConversations();
    } catch (e) {
      alert('Error');
    }
  }

  fetchConversations();
  setInterval(fetchConversations, CONFIG.POLLING_INTERVAL);
});
