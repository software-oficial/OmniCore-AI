import React, { useEffect, useState } from 'react';
import api from '../services/api';

interface Employee {
  id: string;
  username: string;
  role: string;
  permissions: string[];
}

const TeamPage: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newEmployee, setNewEmployee] = useState({ 
    username: '', 
    password: '', 
    role: 'employee', 
    platforms: [] as string[] 
  });
  const [editingUser, setEditingUser] = useState<{ username: string, role: string, platforms: string[] } | null>(null);

  useEffect(() => {
    fetchTeam();
  }, []);

  const fetchTeam = async () => {
    try {
      setLoading(true);
      const response = await api.get('/business/team');
      setEmployees(response.data.data);
    } catch (error) {
      console.error('Error fetching team:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEmployee = async () => {
    try {
      await api.post('/business/team', newEmployee);
      setIsModalOpen(false);
      setNewEmployee({ username: '', password: '', role: 'employee', platforms: [] });
      await fetchTeam();
    } catch (error) {
      alert('Error creating employee');
    }
  };

  const handleUpdateRole = async () => {
    if (!editingUser) return;
    try {
      await api.patch(`/business/team/${editingUser.username}/role`, { 
        role: editingUser.role,
        platforms: editingUser.platforms 
      });
      setEditingUser(null);
      await fetchTeam();
    } catch (error) {
      alert('Error updating role');
    }
  };

  const togglePlatform = (platform: string, currentPlatforms: string[]) => {
    const updated = currentPlatforms.includes(platform)
      ? currentPlatforms.filter(p => p !== platform)
      : [...currentPlatforms, platform];
    
    if (editingUser) {
      setEditingUser({...editingUser, platforms: updated});
    } else {
      setNewEmployee({...newEmployee, platforms: updated});
    }
  };

  if (loading) return <div className="p-8 text-center">Cargando equipo...</div>;

  return (
    <div className="p-6 max-w-5xl mx-auto text-slate-100">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Gestión de Equipo OmniCore</h1>
          <p className="text-sm text-slate-400">Administra los accesos y roles. El Administrador tiene control total sobre todas las plataformas.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)} 
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition shadow-sm"
        >
          + Nuevo Usuario
        </button>
      </div>

      <div className="bg-slate-800 shadow-md rounded-xl overflow-hidden border border-slate-700">
        <table className="w-full text-left border-collapse">
          <thead className="bg-slate-900 text-slate-400 uppercase text-xs font-semibold">
            <tr>
              <th className="px-6 py-3 border-b border-slate-700">Usuario</th>
              <th className="px-6 py-3 border-b border-slate-700">Rol</th>
              <th className="px-6 py-3 border-b border-slate-700">Acceso a Plataformas</th>
              <th className="px-6 py-3 border-b border-slate-700 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {employees.map((emp) => (
              <tr key={emp.id} className="hover:bg-slate-700/50 transition">
                <td className="px-6 py-4 font-medium text-slate-200">{emp.username}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    emp.role === 'admin' ? 'bg-purple-900/30 text-purple-400' : 'bg-slate-700 text-slate-300'
                  }`}>
                    {emp.role}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1">
                    {emp.role === 'admin' ? (
                      <span className="text-[10px] bg-purple-900/30 text-purple-400 px-1.5 py-0.5 rounded border border-purple-900/50 font-bold">FULL ACCESS</span>
                    ) : (
                      emp.permissions.map(p => (
                        <span key={p} className="text-[10px] bg-blue-900/30 text-blue-400 px-1.5 py-0.5 rounded border border-blue-900/50">
                          {p}
                        </span>
                      ))
                    )}
                    {emp.role !== 'admin' && emp.permissions.length === 0 && <span className="text-xs text-slate-500 italic">Sin acceso</span>}
                  </div>
                </td>
                <td className="px-6 py-4 text-right">
                  <button 
                    onClick={() => setEditingUser({ username: emp.username, role: emp.role, platforms: emp.permissions })}
                    className="text-indigo-400 hover:text-indigo-300 text-sm font-medium"
                  >
                    Gestionar Acceso
                  </button>
                </td>
              </tr>
            ))}
            {employees.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                  No hay usuarios registrados.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal for Creating Employee */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl border border-slate-700">
            <h2 className="text-xl font-bold mb-4 text-white">Agregar Usuario</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Nombre de Usuario</label>
                <input 
                  type="text" 
                  value={newEmployee.username}
                  onChange={(e) => setNewEmployee({...newEmployee, username: e.target.value})}
                  className="w-full p-2 border border-slate-700 rounded-lg bg-slate-900 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                  placeholder="ej. juan_ventas"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Contraseña</label>
                <input 
                  type="password" 
                  value={newEmployee.password}
                  onChange={(e) => setNewEmployee({...newEmployee, password: e.target.value})}
                  className="w-full p-2 border border-slate-700 rounded-lg bg-slate-900 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                  placeholder="********"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Rol</label>
                <select 
                  value={newEmployee.role}
                  onChange={(e) => setNewEmployee({...newEmployee, role: e.target.value})}
                  className="w-full p-2 border border-slate-700 rounded-lg bg-slate-900 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                >
                  <option value="employee">Empleado</option>
                  <option value="manager">Gerente</option>
                  <option value="admin">Administrador Global</option>
                </select>
              </div>
              
              {newEmployee.role !== 'admin' && (
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">Acceso a Plataformas</label>
                  <div className="flex flex-wrap gap-2">
                    {['Stock', 'WhatsApp', 'Pagos'].map(platform => (
                      <button
                        key={platform}
                        onClick={() => togglePlatform(platform, newEmployee.platforms)}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium transition ${
                          newEmployee.platforms.includes(platform) 
                          ? 'bg-indigo-600 text-white border-indigo-500' 
                          : 'bg-slate-700 text-slate-400 border-slate-600 hover:bg-slate-600'
                        } border`}
                      >
                        {platform}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button 
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 text-slate-400 hover:bg-slate-700 rounded-lg transition"
              >
                Cancelar
              </button>
              <button 
                onClick={handleCreateEmployee}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
              >
                Crear Usuario
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal for Updating Role */}
      {editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-sm shadow-2xl border border-slate-700">
            <h2 className="text-xl font-bold mb-4 text-white">Gestionar: {editingUser.username}</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Rol</label>
                <select 
                  value={editingUser.role}
                  onChange={(e) => setEditingUser({...editingUser, role: e.target.value})}
                  className="w-full p-2 border border-slate-700 rounded-lg bg-slate-900 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                >
                  <option value="employee">Empleado</option>
                  <option value="manager">Gerente</option>
                  <option value="admin">Administrador Global</option>
                </select>
              </div>

              {editingUser.role !== 'admin' && (
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">Acceso a Plataformas</label>
                  <div className="flex flex-wrap gap-2">
                    {['Stock', 'WhatsApp', 'Pagos'].map(platform => (
                      <button
                        key={platform}
                        onClick={() => togglePlatform(platform, editingUser.platforms)}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium transition ${
                          editingUser.platforms.includes(platform) 
                          ? 'bg-indigo-600 text-white border-indigo-500' 
                          : 'bg-slate-700 text-slate-400 border-slate-600 hover:bg-slate-600'
                        } border`}
                      >
                        {platform}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button 
                onClick={() => setEditingUser(null)}
                className="px-4 py-2 text-slate-400 hover:bg-slate-700 rounded-lg transition"
              >
                Cancelar
              </button>
              <button 
                onClick={handleUpdateRole}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
              >
                Actualizar Acceso
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamPage;
