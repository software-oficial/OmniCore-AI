import React from 'react';

const commands = [
  { key: 'IMPORT_STOCK', desc: 'Importación masiva y mapeo de productos desde CSV.', color: 'var(--accent-stock)' },
  { key: 'GET_SALES', desc: 'Reportes de ventas y movimiento de stock detallado.', color: 'var(--accent-stock)' },
  { key: 'MANAGE_OWNERS', desc: 'Gestión de dueños y asignación de permisos maestros.', color: 'var(--accent-stock)' },
  { key: 'STAFF_CONTROL', desc: 'Control de empleados y acceso restringido a inventario.', color: 'var(--accent-stock)' },
  { key: 'STOCK_SYNC', desc: 'Sincronización de existencias en tiempo real con el backend.', color: 'var(--accent-stock)' },
  { key: 'AUDIT_STOCK', desc: 'Auditoría de ajustes, mermas y correcciones de stock.', color: 'var(--accent-stock)' },
];

const InventoryImportPage: React.FC = () => {
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

export default InventoryImportPage;
