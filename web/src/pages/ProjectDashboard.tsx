import { useEffect, useState, useCallback } from 'react';
import api from '../services/api';
import { Plus, Key, BarChart2, X, Database, Bot, ShieldCheck, Users, Activity, Globe } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  tier: string;
  owner_id: string;
}

const ProjectDashboard = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  
  const [formData, setFormData] = useState({
    agent_name: '',
    tier: 'FREE',
    db_host: '',
    db_port: 5432,
    db_user: '',
    db_password: '',
    db_name: '',
  });

  const fetchProjects = useCallback(async () => {
    try {
      const response = await api.get('/admin/apps');
      setProjects(response.data.data);
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleOnboard = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post('/admin/apps/onboard', formData);
      setIsModalOpen(false);
      setFormData({ agent_name: '', tier: 'FREE', db_host: '', db_port: 5432, db_user: '', db_password: '', db_name: '' });
      await fetchProjects();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error during onboarding');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="p-6 bg-gray-950 min-h-screen text-white">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-end mb-8">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">Panel Maestro OmniCore</h1>
            <p className="text-gray-400 mt-1">Gestión Global de Infraestructura y Clientes SaaS</p>
          </div>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 px-5 py-2.5 rounded-xl text-sm font-bold transition-all shadow-lg shadow-indigo-500/20"
          >
            <Plus size={18}/> Nuevo Cliente (Zero-to-Hero)
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800 flex items-center gap-4">
            <div className="p-3 bg-indigo-500/10 rounded-lg text-indigo-400"><Users size={24}/></div>
            <div>
              <p className="text-xs text-gray-500 uppercase font-semibold">Total Clientes</p>
              <p className="text-2xl font-bold">{projects.length}</p>
            </div>
          </div>
          <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800 flex items-center gap-4">
            <div className="p-3 bg-emerald-500/10 rounded-lg text-emerald-400"><Activity size={24}/></div>
            <div>
              <p className="text-xs text-gray-500 uppercase font-semibold">Sistemas Online</p>
              <p className="text-2xl font-bold">100%</p>
            </div>
          </div>
          <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800 flex items-center gap-4">
            <div className="p-3 bg-blue-500/10 rounded-lg text-blue-400"><Globe size={24}/></div>
            <div>
              <p className="text-xs text-gray-500 uppercase font-semibold">Regiones Activas</p>
              <p className="text-2xl font-bold">1</p>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-12 w-12 border-t-2 border-indigo-500"></div></div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {projects.map((project) => (
              <div key={project.id} className="bg-gray-900 p-5 rounded-2xl border border-gray-800 hover:border-indigo-500/50 transition-all group">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="font-bold text-lg group-hover:text-indigo-400 transition-colors">{project.name}</h2>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                        project.tier === 'ENTERPRISE' ? 'bg-amber-500/10 text-amber-500' : 'bg-indigo-500/10 text-indigo-400'
                      }`}>
                        {project.tier}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 font-mono mt-1">ID: {project.id}</p>
                  </div>
                  <div className="p-2 bg-gray-800 rounded-lg text-gray-400 hover:text-white cursor-pointer">
                    <Key size={16}/>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3 mt-6">
                  <button className="bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-2">
                    <BarChart2 size={14}/> Analíticas
                  </button>
                  <button className="bg-indigo-600/10 text-indigo-400 hover:bg-indigo-600/20 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-2">
                    <Database size={14}/> Infra
                  </button>
                </div>
              </div>
            ))}
            {projects.length === 0 && (
              <div className="col-span-full py-20 text-center border-2 border-dashed border-gray-800 rounded-3xl text-gray-600">
                <Bot size={48} className="mx-auto mb-4 opacity-20"/>
                <p>No hay clientes registrados en el sistema.</p>
              </div>
            )}
          </div>
        )}

        {isModalOpen && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-gray-900 border border-gray-800 w-full max-w-2xl rounded-3xl p-8 shadow-2xl max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h2 className="text-2xl font-bold text-white">Onboarding de Cliente</h2>
                  <p className="text-sm text-gray-400">Configuración instantánea de infraestructura y despliegue de esquemas.</p>
                </div>
                <button onClick={() => setIsModalOpen(false)} className="text-gray-500 hover:text-white transition">
                  <X size={24}/>
                </button>
              </div>
              
              <form onSubmit={handleOnboard} className="space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4 p-5 bg-gray-800/40 rounded-2xl border border-gray-800">
                    <div className="flex items-center gap-2 text-indigo-400 font-bold text-xs uppercase tracking-widest mb-4">
                      <Bot size={16}/> Identidad
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Nombre de la App/Cliente</label>
                      <input 
                        type="text" 
                        placeholder="Ej: Bot Ventas Juan" 
                        className="w-full p-2.5 bg-gray-900 rounded-xl border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                        value={formData.agent_name}
                        onChange={(e) => setFormData({ ...formData, agent_name: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Plan de Suscripción</label>
                      <select 
                        className="w-full p-2.5 bg-gray-900 rounded-xl border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                        value={formData.tier}
                        onChange={(e) => setFormData({ ...formData, tier: e.target.value })}
                      >
                        <option value="FREE">Free (Básico)</option>
                        <option value="PRO">Pro (Avanzado)</option>
                        <option value="ENTERPRISE">Enterprise (Corporativo)</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-4 p-5 bg-gray-800/40 rounded-2xl border border-gray-800">
                    <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase tracking-widest mb-4">
                      <Database size={16}/> Infraestructura DB
                    </div>
                    <div className="grid grid-cols-1 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Host de Base de Datos</label>
                        <input 
                          type="text" 
                          placeholder="db.railway.internal" 
                          className="w-full p-2.5 bg-gray-900 rounded-xl border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                          value={formData.db_host}
                          onChange={(e) => setFormData({ ...formData, db_host: e.target.value })}
                          required
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs font-medium text-gray-500 mb-1">Puerto</label>
                          <input 
                            type="number" 
                            className="w-full p-2.5 bg-gray-900 rounded-xl border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                            value={formData.db_port}
                            onChange={(e) => setFormData({ ...formData, db_port: parseInt(e.target.value) })}
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-500 mb-1">Nombre DB</label>
                          <input 
                            type="text" 
                            placeholder="omnicore_db" 
                            className="w-full p-2.5 bg-gray-900 rounded-xl border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                            value={formData.db_name}
                            onChange={(e) => setFormData({ ...formData, db_name: e.target.value })}
                            required
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs font-medium text-gray-500 mb-1">Usuario</label>
                          <input 
                            type="text" 
                            className="w-full p-2.5 bg-gray-900 rounded-xl border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                            value={formData.db_user}
                            onChange={(e) => setFormData({ ...formData, db_user: e.target.value })}
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-500 mb-1">Password</label>
                          <input 
                            type="password" 
                            className="w-full p-2.5 bg-gray-900 rounded-xl border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                            value={formData.db_password}
                            onChange={(e) => setFormData({ ...formData, db_password: e.target.value })}
                            required
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-4 bg-indigo-900/20 border border-indigo-800/50 rounded-2xl">
                  <ShieldCheck size={20} className="text-indigo-400 mt-0.5 shrink-0"/>
                  <p className="text-xs text-indigo-300 leading-relaxed">
                    El sistema vinculará el agente y ejecutará automáticamente los <strong>Blueprints SQL</strong> en la base de datos proporcionada para garantizar la operatividad inmediata.
                  </p>
                </div>

                <button 
                  type="submit" 
                  disabled={creating}
                  className="w-full py-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 text-white rounded-2xl font-bold transition-all flex items-center justify-center gap-3 shadow-xl shadow-indigo-500/20"
                >
                  {creating ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Desplegando Infraestructura...
                    </>
                  ) : 'Lanzar Cliente SaaS'}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectDashboard;
