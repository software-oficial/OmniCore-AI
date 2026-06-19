import React, { useEffect, useState } from 'react';
import api from '../services/api';

interface ServiceCredential {
  id: string;
  service_type: 'WHATSAPP' | 'MERCADOPAGO' | 'STRIPE' | 'PAYPAL';
  provider_id: string;
  config: Record<string, any>;
  label: string;
  is_active: boolean;
}

const ServiceAccountsPage: React.FC = () => {
  const [accounts, setAccounts] = useState<ServiceCredential[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newAccount, setNewAccount] = useState({
    label: '',
    service_type: 'WHATSAPP',
    provider_id: '',
    config: {},
  });

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/business/credentials');
      setAccounts(response.data.data);
    } catch (error) {
      console.error('Error fetching credentials:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAccount = async () => {
    try {
      await api.post('/business/credentials', newAccount);
      setIsModalOpen(false);
      setNewAccount({ label: '', service_type: 'WHATSAPP', provider_id: '', config: {} });
      await fetchAccounts();
    } catch (error) {
      alert('Error saving service account');
    }
  };

  const toggleAccountStatus = async (id: string, currentStatus: boolean) => {
    try {
      await api.patch(`/business/credentials/${id}/status`, { is_active: !currentStatus });
      await fetchAccounts();
    } catch (error) {
      alert('Error updating status');
    }
  };

  if (loading) return <div className="p-8 text-center">Cargando cuentas de servicio...</div>;

  return (
    <div className="p-6 max-w-5xl mx-auto text-slate-100">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Cuentas de Servicio</h1>
          <p className="text-sm text-slate-400">Gestiona tus instancias de WhatsApp, Pagos y otros proveedores.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)} 
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition shadow-sm"
        >
          + Agregar Cuenta
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accounts.map((acc) => (
          <div key={acc.id} className={`p-6 rounded-2xl border transition shadow-sm hover:shadow-md ${acc.is_active ? 'bg-slate-800 border-slate-700' : 'bg-slate-900/50 border-red-900/30 opacity-75'}`}>
            <div className="flex justify-between items-start mb-4">
              <div className="p-2 bg-blue-900/30 text-blue-400 rounded-lg font-bold text-xs uppercase">
                {acc.service_type}
              </div>
              <span className={`text-xs px-2 py-1 rounded-full ${acc.is_active ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                {acc.is_active ? 'Activa' : 'Inactiva'}
              </span>
            </div>
            <h3 className="text-lg font-bold text-white mb-1">{acc.label}</h3>
            <p className="text-sm text-slate-400 mb-4 font-mono">{acc.provider_id}</p>
            
            <div className="flex justify-end space-x-2">
              <button 
                onClick={() => toggleAccountStatus(acc.id, acc.is_active)}
                className={`text-sm font-medium ${acc.is_active ? 'text-red-400 hover:text-red-300' : 'text-green-400 hover:text-green-300'}`}
              >
                {acc.is_active ? 'Desactivar' : 'Activar'}
              </button>
              <button className="text-sm font-medium text-blue-400 hover:text-blue-300">Configurar</button>
            </div>
          </div>
        ))}
        {accounts.length === 0 && (
          <div className="col-span-full p-12 text-center bg-slate-800/50 rounded-2xl border-2 border-dashed border-slate-700 text-slate-500">
            No hay cuentas de servicio configuradas.
          </div>
        )}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl border border-slate-700">
            <h2 className="text-xl font-bold mb-4 text-white">Nueva Cuenta de Servicio</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Etiqueta (Label)</label>
                <input 
                  type="text" 
                  value={newAccount.label}
                  onChange={(e) => setNewAccount({...newAccount, label: e.target.value})}
                  className="w-full p-2 border border-slate-700 rounded-lg bg-slate-900 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="ej. Bot Ventas Centro"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Tipo de Servicio</label>
                <select 
                  value={newAccount.service_type}
                  onChange={(e) => setNewAccount({...newAccount, service_type: e.target.value as any})}
                  className="w-full p-2 border border-slate-700 rounded-lg bg-slate-900 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="WHATSAPP">WhatsApp</option>
                  <option value="MERCADOPAGO">Mercado Pago</option>
                  <option value="STRIPE">Stripe</option>
                  <option value="PAYPAL">PayPal</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">ID del Proveedor</label>
                <input 
                  type="text" 
                  value={newAccount.provider_id}
                  onChange={(e) => setNewAccount({...newAccount, provider_id: e.target.value})}
                  className="w-full p-2 border border-slate-700 rounded-lg bg-slate-900 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="ID externo o número de teléfono"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button 
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 text-slate-400 hover:bg-slate-700 rounded-lg transition"
              >
                Cancelar
              </button>
              <button 
                onClick={handleSaveAccount}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Guardar Cuenta
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ServiceAccountsPage;
