import React, { useEffect, useState } from 'react';
import api from '../services/api';

interface Setting {
  setting_key: string;
  setting_value: string;
  description?: string;
}

const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [newSetting, setNewSetting] = useState({ key: '', value: '', description: '' });
  const [editingKey, setEditingKey] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await api.get('/business/settings');
      setSettings(response.data.data);
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSetting = async () => {
    try {
      const payload = {
        key: editingKey || newSetting.key,
        value: editingKey ? settings[editingKey] : newSetting.value, // This logic is simplified for the demo
        description: newSetting.description
      };
      
      // If editing, we use the current value or we can add a field to update it
      // For this implementation, let's assume the user provides a new value in a modal
      
      await api.patch('/business/settings', payload);
      setNewSetting({ key: '', value: '', description: '' });
      setEditingKey(null);
      await fetchSettings();
    } catch (error) {
      alert('Error saving setting');
    }
  };

  if (loading) return <div className="p-8 text-center">Cargando configuraciones...</div>;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Configuración del Negocio</h1>
        <button 
          onClick={() => setEditingKey(null)} 
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          + Agregar Variable
        </button>
      </div>

      <div className="bg-white shadow-md rounded-xl overflow-hidden border border-gray-200">
        <table className="w-full text-left border-collapse">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs font-semibold">
            <tr>
              <th className="px-6 py-3 border-b">Llave</th>
              <th className="px-6 py-3 border-b">Valor</th>
              <th className="px-6 py-3 border-b">Descripción</th>
              <th className="px-6 py-3 border-b text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {Object.entries(settings).map(([key, value]) => (
              <tr key={key} className="hover:bg-gray-50 transition">
                <td className="px-6 py-4 font-mono text-sm text-blue-600">{key}</td>
                <td className="px-6 py-4 text-sm text-gray-700">{value}</td>
                <td className="px-6 py-4 text-sm text-gray-500 italic">No provista</td>
                <td className="px-6 py-4 text-right">
                  <button 
                    onClick={() => setEditingKey(key)}
                    className="text-blue-500 hover:text-blue-700 text-sm font-medium"
                  >
                    Editar
                  </button>
                </td>
              </tr>
            ))}
            {Object.keys(settings).length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-400">
                  No hay configuraciones definidas aún.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Basic Modal for Adding/Editing */}
      { (editingKey || newSetting.key) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <h2 className="text-xl font-bold mb-4">
              {editingKey ? `Editar ${editingKey}` : 'Nueva Variable'}
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Llave (Key)</label>
                <input 
                  type="text" 
                  disabled={!!editingKey}
                  value={editingKey || newSetting.key}
                  onChange={(e) => setNewSetting({...newSetting, key: e.target.value})}
                  className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="ej. whatsapp_api_token"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Valor (Value)</label>
                <input 
                  type="text" 
                  value={newSetting.value}
                  onChange={(e) => setNewSetting({...newSetting, value: e.target.value})}
                  className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Valor de la configuración"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
                <textarea 
                  value={newSetting.description}
                  onChange={(e) => setNewSetting({...newSetting, description: e.target.value})}
                  className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="Para qué sirve esta variable..."
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button 
                onClick={() => {setEditingKey(null); setNewSetting({key:'', value:'', description:''})}}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition"
              >
                Cancelar
              </button>
              <button 
                onClick={handleSaveSetting}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Guardar Cambios
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
