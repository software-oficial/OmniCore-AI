import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Home, Key, LayoutGrid } from 'lucide-react';

interface MobileLayoutProps {
  children: React.ReactNode;
}

const MobileLayout: React.FC<MobileLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/apps', icon: Home, label: 'Inicio' },
    { path: '/projects', icon: LayoutGrid, label: 'Proyectos' },
    { path: '/tokens', icon: Key, label: 'Tokens' },
  ];

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      <main className="flex-1 overflow-y-auto p-4 pb-20">
        {children}
      </main>
      
      <nav className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 flex justify-around p-3">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <button 
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`flex flex-col items-center ${isActive ? 'text-indigo-400' : 'text-gray-400'}`}
            >
              <Icon size={24} />
              <span className="text-xs">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export default MobileLayout;
