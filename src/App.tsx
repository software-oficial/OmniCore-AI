import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Layout from './components/Layout';
import AuditPage from './pages/AuditPage';
import InventoryImportPage from './pages/InventoryImportPage';
import SettingsPage from './pages/SettingsPage';
import TeamPage from './pages/TeamPage';
import WhatsAppPage from './pages/WhatsAppPage';
import PaymentPage from './pages/PaymentPage';
import ServiceAccountsPage from './pages/ServiceAccountsPage';

const Home: React.FC = () => {
  const modules = [
    { name: 'Stock & Gestión', path: '/stock', color: 'var(--accent-stock)', icon: '📦' },
    { name: 'WhatsApp Bot', path: '/whatsapp', color: 'var(--accent-whatsapp)', icon: '🤖' },
    { name: 'Pasarela de Pagos', path: '/pagos', color: 'var(--accent-payments)', icon: '💳' },
  ];

  return (
    <div className="omnicore-container">
      <div className="omnicore-header">
        <h1>OmniCore AI</h1>
        <p className="text-slate-400">Panel Central de Control Operativo</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {modules.map(mod => (
          <Link 
            key={mod.path} 
            to={mod.path} 
            className="module-link-card" 
            style={{ '--accent-color': mod.color } as any}
          >
            <div className="text-5xl mb-4">{mod.icon}</div>
            <h2 className="text-xl font-bold mb-2">{mod.name}</h2>
            <p className="text-sm text-slate-400 mb-6">Acceder a los comandos de {mod.name.toLowerCase()}.</p>
            <div className="btn-run" style={{ backgroundColor: mod.color }}>Entrar al Módulo</div>
          </Link>
        ))}
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/stock" element={<InventoryImportPage />} />
          <Route path="/whatsapp" element={<WhatsAppPage />} />
          <Route path="/pagos" element={<PaymentPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/team" element={<TeamPage />} />
          <Route path="/accounts" element={<ServiceAccountsPage />} />
          <Route path="/" element={<Home />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
