import React from 'react';
import { Link } from 'react-router-dom';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-slate-900 text-slate-100">
      {/* Sidebar */}
      <nav className="w-64 bg-slate-800 border-r border-slate-700 p-6 flex flex-col">
        <div className="text-xl font-bold mb-10 text-cyan-400 flex items-center gap-2">
          <span>🤖</span> OmniCore AI
        </div>
        
        <div className="flex flex-col gap-2 flex-1">
          <p className="text-xs font-semibold text-slate-500 uppercase mb-2">Módulos</p>
          <Link to="/stock" className="p-2 hover:bg-slate-700 rounded-lg transition flex items-center gap-3">
            <span>📦</span> Gestión de Stock
          </Link>
          <Link to="/whatsapp" className="p-2 hover:bg-slate-700 rounded-lg transition flex items-center gap-3">
            <span>💬</span> WhatsApp Bot
          </Link>
          <Link to="/pagos" className="p-2 hover:bg-slate-700 rounded-lg transition flex items-center gap-3">
            <span>💳</span> Pasarela de Pagos
          </Link>
          
          <div className="my-4 border-t border-slate-700"></div>
          <p className="text-xs font-semibold text-slate-500 uppercase mb-2">Administración</p>
          <Link to="/audit" className="p-2 hover:bg-slate-700 rounded-lg transition flex items-center gap-3">
            <span>📜</span> Auditoría
          </Link>
          <Link to="/settings" className="p-2 hover:bg-slate-700 rounded-lg transition flex items-center gap-3">
            <span>⚙️</span> Ajustes
          </Link>
          <Link to="/team" className="p-2 hover:bg-slate-700 rounded-lg transition flex items-center gap-3">
            <span>👥</span> Equipo
          </Link>
        </div>
        
        <div className="text-xs text-slate-500 text-center mt-auto">
          OmniCore Client v1.0
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 p-8 overflow-y-auto">
        {children}
      </main>
    </div>
  );
};

export default Layout;
