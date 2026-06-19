import React, { useEffect, useState } from 'react';
import api from '../services/api';

interface WhatsAppAccount {
  id: string;
  label: string;
}

const WhatsAppPage: React.FC = () => {
  const [accounts, setAccounts] = useState<WhatsAppAccount[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/business/credentials?service_type=WHATSAPP');
      setAccounts(response.data.data);
      if (response.data.data.length > 0) {
        setSelectedAccount(response.data.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching WhatsApp accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-center">Cargando cuentas de WhatsApp...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Configuración de WhatsApp</h1>
        <div className="flex items-center space-x-3">
          <label className="text-sm font-medium text-gray-600">Instancia:</label>
          <select 
            value={selectedAccount}
            onChange={(e) => setSelectedAccount(e.target.value)}
            className="p-2 border rounded-lg bg-white shadow-sm focus:ring-2 focus:ring-blue-500 outline-none"
          >
            {accounts.map(acc => (
              <option key={acc.id} value={acc.id}>{acc.label}</option>
            ))}
          </select>
        </div>
      </div>

      {selectedAccount ? (
        <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-xl">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Panel de Control de Bot</h2>
            <span className="text-xs bg-cyan-500/20 text-cyan-400 px-2 py-1 rounded-full border border-cyan-500/30">
              ID: {selectedAccount}
            </span>
          </div>
          
          <p className="text-slate-400 mb-6">Gestión de flujos y respuestas automatizadas para esta instancia.</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-slate-900 rounded-lg border border-slate-700">
              <p className="text-xs text-slate-500 uppercase mb-2">Estado del Bot</p>
              <div className="flex items-center space-x-2 text-green-400 font-mono">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span>Conectado y Operativo</span>
              </div>
            </div>
            <div className="p-4 bg-slate-900 rounded-lg border border-slate-700">
              <p className="text-xs text-slate-500 uppercase mb-2">Modo Actual</p>
              <div className="text-cyan-400 font-mono">
                🤖 Automatizado (Bot Flow)
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-slate-900 rounded-lg border border-slate-700 text-cyan-400 font-mono text-sm">
            // El bot está operando con la configuración de la instancia seleccionada.
          </div>
        </div>
      ) : (
        <div className="p-12 text-center bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200 text-gray-400">
          No hay cuentas de WhatsApp configuradas. Por favor, agréguelas en "Cuentas de Servicio".
        </div>
      )}
    </div>
  );
};

export default WhatsAppPage;
