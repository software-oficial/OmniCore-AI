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
    <div className="p-6 max-w-6xl mx-auto text-slate-100">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Trazabilidad y Auditoría</h1>
          <p className="text-sm text-slate-400">Historial detallado de todas las acciones ejecutadas en el sistema.</p>
        </div>
        <div className="flex space-x-2">
          <input 
            type="text" 
            placeholder="Filtrar por comando..." 
            value={filterCommand}
            onChange={(e) => { setFilterCommand(e.target.value); setPage(0); }}
            className="p-2 border border-slate-700 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 bg-slate-800 text-white"
          />
        </div>
      </div>

      <div className="bg-slate-800 shadow-md rounded-xl overflow-hidden border border-slate-700">
        <table className="w-full text-left border-collapse">
          <thead className="bg-slate-900 text-slate-400 uppercase text-xs font-semibold">
            <tr>
              <th className="px-6 py-3 border-b border-slate-700">Fecha y Hora</th>
              <th className="px-6 py-3 border-b border-slate-700">Agente</th>
              <th className="px-6 py-3 border-b border-slate-700">Comando</th>
              <th className="px-6 py-3 border-b border-slate-700">Estado</th>
              <th className="px-6 py-3 border-b border-slate-700">Mensaje</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-slate-700/50 transition">
                <td className="px-6 py-4 text-xs text-slate-400 whitespace-nowrap">
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td className="px-6 py-4 text-sm font-mono text-slate-300">{log.agent_id}</td>
                <td className="px-6 py-4 text-sm font-medium text-cyan-400">{log.command}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase ${
                    log.status === 'SUCCESS' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                  }`}>
                    {log.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-slate-300 truncate max-w-xs">{log.message}</td>
              </tr>
            ))}
            {logs.length === 0 && !loading && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
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
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm hover:bg-slate-700 disabled:opacity-50 transition text-slate-300"
        >
          Anterior
        </button>
        <span className="text-sm text-slate-400">Página {page + 1}</span>
        <button 
          disabled={logs.length < LIMIT}
          onClick={() => setPage(p => p + 1)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm hover:bg-slate-700 disabled:opacity-50 transition text-slate-300"
        >
          Siguiente
        </button>
      </div>
    </div>
  );
  }
;

export default AuditPage;
