import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import AuditPage from './pages/AuditPage';
import InventoryImportPage from './pages/InventoryImportPage';
import SettingsPage from './pages/SettingsPage';
import TeamPage from './pages/TeamPage';
import WhatsAppPage from './pages/WhatsAppPage';
import PaymentPage from './pages/PaymentPage';
import ServiceAccountsPage from './pages/ServiceAccountsPage';

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
          <Route path="/" element={<div className="p-10 text-center">Bienvenido al Panel de Clientes de OmniCore-AI. <br/> Seleccione un módulo en el menú lateral.</div>} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
