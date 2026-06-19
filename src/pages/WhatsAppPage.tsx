import React, { useState } from 'react';
import api from '../services/api';

const commands = [
  { key: 'SET_CHAT_MENU', desc: 'Configura los menús interactivos y la navegación del chat.', endpoint: '/business/credentials', method: 'GET', color: 'var(--accent-whatsapp)' },
  { key: 'AUTO_SALES_FLOW', desc: 'Gestiona flujos de ventas automatizadas y embudos.', endpoint: '/business/credentials', method: 'GET', color: 'var(--accent-whatsapp)' },
  { key: 'BOT_RESPONSE_EDIT', desc: 'Edita respuestas automáticas y plantillas del bot.', endpoint: '/business/credentials', method: 'GET', color: 'var(--accent-whatsapp)' },
  { key: 'GET_INSTANCES', desc: 'Lista y monitorea instancias activas de WhatsApp.', endpoint: '/business/credentials?service_type=WHATSAPP', method: 'GET', color: 'var(--accent-whatsapp)' },
  { key: 'CHAT_AUDIT', desc: 'Revisa el historial de interacciones y logs del bot.', endpoint: '/audit', method: 'GET', color: 'var(--accent-whatsapp)' },
  { key: 'RESTART_BOT', desc: 'Reinicia el motor de automatización y refresca sesión.', endpoint: '/business/credentials', method: 'PATCH', color: 'var(--accent-whatsapp)' },
];

const WhatsAppPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{success: boolean, message: string} | null>(null);

  const executeCommand = async (cmd: typeof commands[0]) => {
    setLoading(true);
    setResult(null);
    try {
      const response = await api[cmd.method.toLowerCase() as 'get' | 'post' | 'patch'](cmd.endpoint, cmd.method === 'GET' ? undefined : {});
      setResult({ success: true, message: response.data.message || 'Comando ejecutado exitosamente' });
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.response?.data?.message || 'Error al ejecutar el comando';
      setResult({ success: false, message: msg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="omnicore-container">
      <div className="omnicore-header">
        <h1>WhatsApp Bot</h1>
        <p className="text-slate-400">Automatización de Ventas y Atención al Cliente</p>
      </div>

      <div className="command-grid">
        {commands.map(cmd => (
          <div 
            key={cmd.key} 
            className={`command-card ${loading ? 'opacity-50 pointer-events-none' : ''}`} 
            style={{ '--accent-color': cmd.color } as any}
            onClick={() => executeCommand(cmd)}
          >
            <div>
              <span className="command-key">{cmd.key}</span>
              <p className="command-desc">{cmd.desc}</p>
            </div>
            <div className={`btn-run ${loading ? 'animate-pulse' : ''}`}>
              {loading ? 'Ejecutando...' : 'Ejecutar Comando'}
            </div>
          </div>
        ))}
      </div>

      {result && (
        <div className={`fixed bottom-8 right-8 p-4 rounded-xl shadow-2xl border animate-in slide-in-from-bottom-4 duration-300 ${
          result.success ? 'bg-green-900/80 border-green-500 text-green-100' : 'bg-red-900/80 border-red-500 text-red-100'
        }`}>
          <p className="text-sm font-medium">{result.message}</p>
        </div>
      )}
    </div>
  );
};

export default WhatsAppPage;
