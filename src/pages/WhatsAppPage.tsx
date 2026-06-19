import React from 'react';

const WhatsAppPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Configuración de WhatsApp</h1>
      <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-xl">
        <p className="text-slate-400">Módulo de gestión de bots y flujos de conversación.</p>
        <div className="mt-4 p-4 bg-slate-900 rounded-lg border border-slate-700 text-cyan-400 font-mono text-sm">
          // El bot está conectado al backend de main...
        </div>
      </div>
    </div>
  );
};

export default WhatsAppPage;
