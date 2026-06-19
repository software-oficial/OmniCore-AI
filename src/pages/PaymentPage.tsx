import React, { useEffect, useState } from 'react';
import api from '../services/api';

interface PaymentAccount {
  id: string;
  label: string;
}

const PaymentPage: React.FC = () => {
  const [accounts, setAccounts] = useState<PaymentAccount[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/business/credentials?service_type=MERCADOPAGO');
      setAccounts(response.data.data);
      if (response.data.data.length > 0) {
        setSelectedAccount(response.data.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching payment accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-center">Cargando cuentas de pago...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Pasarela de Pagos</h1>
        <div className="flex items-center space-x-3">
          <label className="text-sm font-medium text-gray-600">Cuenta de Pago:</label>
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
          <p className="text-slate-400 mb-6">Gestión de transacciones, cupones y métodos de pago para la instancia seleccionada.</p>
          <div className="grid grid-cols-3 gap-4 mt-6">
            <div className="p-4 bg-slate-900 rounded-lg border border-slate-700 text-center">
              <p className="text-xs text-slate-500 uppercase">Ventas Hoy</p>
              <p className="text-2xl font-bold text-green-400">$0.00</p>
            </div>
            <div className="p-4 bg-slate-900 rounded-lg border border-slate-700 text-center">
              <p className="text-xs text-slate-500 uppercase">Transacciones</p>
              <p className="text-2xl font-bold text-cyan-400">0</p>
            </div>
            <div className="p-4 bg-slate-900 rounded-lg border border-slate-700 text-center">
              <p className="text-xs text-slate-500 uppercase">Errores</p>
              <p className="text-2xl font-bold text-red-400">0</p>
            </div>
          </div>
          <div className="mt-6 p-4 bg-slate-900 rounded-lg border border-slate-700 text-cyan-400 font-mono text-sm">
            // Los datos mostrados corresponden a la instancia: {selectedAccount}
          </div>
        </div>
      ) : (
        <div className="p-12 text-center bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200 text-gray-400">
          No hay cuentas de pago configuradas. Por favor, agréguelas en "Cuentas de Servicio".
        </div>
      )}
    </div>
  );
};

export default PaymentPage;
