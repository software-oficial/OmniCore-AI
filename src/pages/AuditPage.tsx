import React, { useEffect, useState } from 'react';
import api from '../services/api';

interface AuditLog {
  id: number;
  agent_id: string;
  command: string;
  status: string;
  message: string;
  timestamp: string;
}

const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterCommand, setFilterCommand] = useState('');
  const [page, setPage] = useState(0);
  const LIMIT = 50;

  useEffect(() => {
    fetchLogs();
  }, [page, filterCommand]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await api.get('/business/audit', {
        params: {
          limit: LIMIT,
          offset: page * LIMIT,
          command: filterCommand || undefined,
        },
      });
      setLogs(response.data.data);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Trazabilidad y Auditoría</h1>
          <p className="text-sm text-gray-500">Historial detallado de todas las acciones ejecutadas en el sistema.</p>
        </div>
        <div className="flex space-x-2">
          <input 
            type="text" 
            placeholder="Filtrar por comando..." 
            value={filterCommand}
            onChange={(e) => { setFilterCommand(e.target.value); setPage(0); }}
            className="p-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="bg-white shadow-md rounded-xl overflow-hidden border border-gray-200">
        <table className="w-full text-left border-collapse">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs font-semibold">
            <tr>
              <th className="px-6 py-3 border-b">Fecha y Hora</th>
              <th className="px-6 py-3 border-b">Agente</th>
              <th className="px-6 py-3 border-b">Comando</th>
              <th className="px-6 py-3 border-b">Estado</th>
              <th className="px-6 py-3 border-b">Mensaje</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-gray-50 transition">
                <td className="px-6 py-4 text-xs text-gray-500 whitespace-nowrap">
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td className="px-6 py-4 text-sm font-mono text-gray-600">{log.agent_id}</td>
                <td className="px-6 py-4 text-sm font-medium text-blue-600">{log.command}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase ${
                    log.status === 'SUCCESS' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {log.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600 truncate max-w-xs">{log.message}</td>
              </tr>
            ))}
            {logs.length === 0 && !loading && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-400">
                  No se encontraron registros de auditoría.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-center items-center space-x-4 mt-6">
        <button 
          disabled={page === 0}
          onClick={() => setPage(p => p - 1)}
          className="px-4 py-2 bg-white border rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 transition"
        >
          Anterior
        </button>
        <span className="text-sm text-gray-600">Página {page + 1}</span>
        <button 
          disabled={logs.length < LIMIT}
          onClick={() => setPage(p => p + 1)}
          className="px-4 py-2 bg-white border rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 transition"
        >
          Siguiente
        </button>
      </div>
    </div>
  );
};

export default AuditPage;
