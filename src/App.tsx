import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AuditPage from './pages/AuditPage';
import InventoryImportPage from './pages/InventoryImportPage';
import SettingsPage from './pages/SettingsPage';
import TeamPage from './pages/TeamPage';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/inventory" element={<InventoryImportPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/team" element={<TeamPage />} />
        <Route path="/" element={<div className="p-10 text-center">Bienvenido al Panel de Clientes de OmniCore-AI. Use las rutas /audit, /inventory, /settings o /team.</div>} />
      </Routes>
    </Router>
  );
};

export default App;
