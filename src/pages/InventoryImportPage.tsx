import React, { useState } from 'react';
import api from '../services/api';

const commands = [
  { key: 'IMPORT_STOCK', desc: 'Importación masiva y mapeo de productos desde CSV.', endpoint: '/import/execute', method: 'POST', color: 'var(--accent-stock)' },
  { key: 'GET_SALES', desc: 'Reportes de ventas y movimiento de stock detallado.', endpoint: '/products', method: 'GET', color: 'var(--accent-stock)' },
  { key: 'MANAGE_OWNERS', desc: 'Gestión de dueños y asignación de permisos maestros.', endpoint: '/team', method: 'GET', color: 'var(--accent-stock)' },
  { key: 'STAFF_CONTROL', desc: 'Control de empleados y acceso restringido a inventario.', endpoint: '/team', method: 'GET', color: 'var(--accent-stock)' },
  { key: 'STOCK_SYNC', desc: 'Sincronización de existencias en tiempo real con el backend.', endpoint: '/import/execute', method: 'POST', color: 'var(--accent-stock)' },
  { key: 'AUDIT_STOCK', desc: 'Auditoría de ajustes, mermas y correcciones de stock.', endpoint: '/audit', method: 'GET', color: 'var(--accent-stock)' },
];

const InventoryImportPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{success: boolean, message: string} | null>(null);

  const executeCommand = async (cmd: typeof commands[0]) => {
    setLoading(true);
    setResult(null);
    try {
      const response = await api[cmd.method.toLowerCase() as 'get' | 'post'](cmd.endpoint, cmd.method === 'POST' ? {} : null);
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
        <h1>Stock & Gestión</h1>
        <p className="text-slate-400">Control de Inventario y Administración de Personal</p>
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

export default InventoryImportPage;
