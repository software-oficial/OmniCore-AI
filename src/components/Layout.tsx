import React from 'react';
import { Link } from 'react-router-dom';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <nav className="w-64 bg-slate-900 border-r border-slate-800 p-6 flex flex-col shadow-xl">
        <div className="text-xl font-bold mb-10 text-cyan-400 flex items-center gap-2">
          <span>🤖</span> OmniCore AI
        </div>
        
        <div className="flex flex-col gap-1 flex-1">
          <p className="text-[10px] font-bold text-slate-500 uppercase mb-3 tracking-widest px-2">Módulos</p>
          <Link to="/stock" className="p-2.5 hover:bg-slate-800 rounded-xl transition flex items-center gap-3 text-sm font-medium text-slate-300 hover:text-white">
            <span>📦</span> Gestión de Stock
          </Link>
          <Link to="/whatsapp" className="p-2.5 hover:bg-slate-800 rounded-xl transition flex items-center gap-3 text-sm font-medium text-slate-300 hover:text-white">
            <span>💬</span> WhatsApp Bot
          </Link>
          <Link to="/pagos" className="p-2.5 hover:bg-slate-800 rounded-xl transition flex items-center gap-3 text-sm font-medium text-slate-300 hover:text-white">
            <span>💳</span> Pasarela de Pagos
          </Link>
          <Link to="/accounts" className="p-2.5 hover:bg-slate-800 rounded-xl transition flex items-center gap-3 text-sm font-medium text-slate-300 hover:text-white">
            <span>🔑</span> Cuentas de Servicio
          </Link>
          
          <div className="my-6 border-t border-slate-800"></div>
          <p className="text-[10px] font-bold text-slate-500 uppercase mb-3 tracking-widest px-2">Administración</p>
          <Link to="/audit" className="p-2.5 hover:bg-slate-800 rounded-xl transition flex items-center gap-3 text-sm font-medium text-slate-300 hover:text-white">
            <span>📜</span> Auditoría
          </Link>
          <Link to="/settings" className="p-2.5 hover:bg-slate-800 rounded-xl transition flex items-center gap-3 text-sm font-medium text-slate-300 hover:text-white">
            <span>⚙️</span> Ajustes
          </Link>
          <Link to="/team" className="p-2.5 hover:bg-slate-800 rounded-xl transition flex items-center gap-3 text-sm font-medium text-slate-300 hover:text-white">
            <span>👥</span> Equipo
          </Link>
        </div>
        
        <div className="text-[10px] text-slate-600 text-center mt-auto font-mono">
          v1.0.0-stable
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto relative">
        {children}
      </main>
    </div>
  );
};

export default Layout;
