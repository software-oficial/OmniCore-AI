import React from 'react';

const commands = [
  { key: 'SET_CHAT_MENU', desc: 'Configura los menús interactivos y la navegación del chat.', color: 'var(--accent-whatsapp)' },
  { key: 'AUTO_SALES_FLOW', desc: 'Gestiona flujos de ventas automatizadas y embudos.', color: 'var(--accent-whatsapp)' },
  { key: 'BOT_RESPONSE_EDIT', desc: 'Edita respuestas automáticas y plantillas del bot.', color: 'var(--accent-whatsapp)' },
  { key: 'GET_INSTANCES', desc: 'Lista y monitorea instancias activas de WhatsApp.', color: 'var(--accent-whatsapp)' },
  { key: 'CHAT_AUDIT', desc: 'Revisa el historial de interacciones y logs del bot.', color: 'var(--accent-whatsapp)' },
  { key: 'RESTART_BOT', desc: 'Reinicia el motor de automatización y refresca sesión.', color: 'var(--accent-whatsapp)' },
];

const WhatsAppPage: React.FC = () => {
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
            className="command-card" 
            style={{ '--accent-color': cmd.color } as any}
            onClick={() => alert(`Ejecutando comando: ${cmd.key}`)}
          >
            <div>
              <span className="command-key">{cmd.key}</span>
              <p className="command-desc">{cmd.desc}</p>
            </div>
            <div className="btn-run">Ejecutar Comando</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WhatsAppPage;
