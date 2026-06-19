import React from 'react';
import { NavLink } from 'react-router-dom';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navItemStyles = ({ isActive }: { isActive: boolean }) => 
    `p-2.5 rounded-xl transition-all duration-200 flex items-center gap-3 text-sm font-medium ${
      isActive 
        ? 'bg-indigo-600/20 text-indigo-400 shadow-[inset_0_0_0_1px_rgba(99,102,241,0.4)]' 
        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
    }`;

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <nav className="w-64 bg-slate-900 border-r border-slate-800 p-6 flex flex-col shadow-2xl z-10">
        <div className="text-xl font-extrabold mb-10 text-white flex items-center gap-3 tracking-tight">
          <div className="p-2 bg-cyan-500 rounded-lg shadow-[0_0_15px_rgba(6,182,212,0.4)]">
            <span className="text-lg">🤖</span>
          </div>
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
            OmniCore AI
          </span>
        </div>
        
        <div className="flex flex-col gap-1 flex-1">
          <div className="flex items-center gap-2 mb-4 px-2">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Módulos</p>
            <div className="h-px flex-1 bg-slate-800"></div>
          </div>
          
          <NavLink to="/stock" className={navItemStyles}>
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800 text-sm shadow-sm group-hover:bg-indigo-500/20">📦</span> 
            Gestión de Stock
          </NavLink>
          <NavLink to="/whatsapp" className={navItemStyles}>
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800 text-sm shadow-sm">💬</span> 
            WhatsApp Bot
          </NavLink>
          <NavLink to="/pagos" className={navItemStyles}>
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800 text-sm shadow-sm">💳</span> 
            Pasarela de Pagos
          </NavLink>
          <NavLink to="/accounts" className={navItemStyles}>
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800 text-sm shadow-sm">🔑</span> 
            Cuentas de Servicio
          </NavLink>
          
          <div className="my-8"></div>
          
          <div className="flex items-center gap-2 mb-4 px-2">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Administración</p>
            <div className="h-px flex-1 bg-slate-800"></div>
          </div>
          
          <NavLink to="/audit" className={navItemStyles}>
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800 text-sm shadow-sm">📜</span> 
            Auditoría
          </NavLink>
          <NavLink to="/settings" className={navItemStyles}>
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800 text-sm shadow-sm">⚙️</span> 
            Ajustes
          </NavLink>
          <NavLink to="/team" className={navItemStyles}>
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800 text-sm shadow-sm">👥</span> 
            Equipo
          </NavLink>
        </div>
        
        <div className="mt-auto pt-6 border-t border-slate-800">
          <div className="px-4 py-3 bg-slate-800/50 rounded-2xl border border-slate-700/50 text-center">
            <p className="text-[10px] font-mono text-slate-500 uppercase tracking-tighter">System Status</p>
            <div className="flex items-center justify-center gap-2 mt-1">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-[11px] font-bold text-slate-300">v1.0.0-stable</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto relative bg-slate-950">
        {children}
      </main>
    </div>
  );
};

export default Layout;
