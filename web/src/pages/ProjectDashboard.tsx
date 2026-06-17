import { useEffect, useState, useCallback } from 'react';
import api from '../services/api';
import { Plus, Key, BarChart2, X, Database, Bot, ShieldCheck } from 'lucide-react';

interface Project {
  id: string;
  name: string;
}

const ProjectDashboard = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  
  // Onboarding Form State
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
      const response = await api.get('/agent/projects');
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      await fetchProjects();
    };
    init();
  }, [fetchProjects]);

  const handleOnboard = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      // Zero-to-Hero Flow: Registers agent AND deploys schema
      await api.post('/agent/onboard', formData);
      setIsModalOpen(false);
      setFormData({
        agent_name: '',
        tier: 'FREE',
        db_host: '',
        db_port: 5432,
        db_user: '',
        db_password: '',
        db_name: '',
      });
      await fetchProjects();
    } catch (error: any) {
      console.error('Error during onboarding:', error);
      const msg = error.response?.data?.message || 'Error during onboarding';
      alert(msg);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Mis Proyectos</h1>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={18}/> Nuevo Agente (Zero-to-Hero)
        </button>
      </div>

      {loading ? (
        <p className="text-gray-400">Cargando...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {projects.map((project) => (
            <div key={project.id} className="bg-gray-800 p-4 rounded-xl border border-gray-700 hover:border-indigo-500 transition-colors">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="font-semibold text-lg">{project.name}</h2>
                  <p className="text-xs text-gray-500 font-mono mt-1">ID: {project.id}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button className="flex-1 bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600/30 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <Key size={16}/> Tokens
                </button>
                <button className="flex-1 bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <BarChart2 size={16}/> Uso
                </button>
              </div>
            </div>
          ))}
          {projects.length === 0 && (
            <div className="col-span-full py-12 text-center border-2 border-dashed border-gray-700 rounded-xl text-gray-500">
              No tienes agentes activos. ¡Despliega tu primero en segundos!
            </div>
          )}
        </div>
      )}

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-700 w-full max-w-2xl rounded-2xl p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-xl font-bold">Onboarding Zero-to-Hero</h2>
                <p className="text-sm text-gray-400">Registra tu agente y despliega la infraestructura automáticamente.</p>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-white">
                <X size={24}/>
              </button>
            </div>
            
            <form onSubmit={handleOnboard} className="space-y-6">
              {/* Agent Section */}
              <div className="space-y-4 p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm uppercase tracking-wider">
                  <Bot size={16}/> Identidad del Agente
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Nombre del Agente</label>
                    <input 
                      autoFocus
                      type="text" 
                      placeholder="Ej: Bot Ventas" 
                      className="w-full p-2 bg-gray-800 rounded-lg border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={formData.agent_name}
                      onChange={(e) => setFormData({ ...formData, agent_name: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Tier de Servicio</label>
                    <select 
                      className="w-full p-2 bg-gray-800 rounded-lg border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={formData.tier}
                      onChange={(e) => setFormData({ ...formData, tier: e.target.value })}
                    >
                      <option value="FREE">Free (Básico)</option>
                      <option value="PRO">Pro (Avanzado)</option>
                      <option value="ENTERPRISE">Enterprise (Corporativo)</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Database Section */}
              <div className="space-y-4 p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm uppercase tracking-wider">
                  <Database size={16}/> Configuración de Base de Datos
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-xs font-medium text-gray-400 mb-1">Host de la DB</label>
                    <input 
                      type="text" 
                      placeholder="postgres.railway.internal o localhost" 
                      className="w-full p-2 bg-gray-800 rounded-lg border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={formData.db_host}
                      onChange={(e) => setFormData({ ...formData, db_host: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Puerto</label>
                    <input 
                      type="number" 
                      className="w-full p-2 bg-gray-800 rounded-lg border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={formData.db_port}
                      onChange={(e) => setFormData({ ...formData, db_port: parseInt(e.target.value) })}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Nombre de la DB</label>
                    <input 
                      type="text" 
                      placeholder="omnicore_biz" 
                      className="w-full p-2 bg-gray-800 rounded-lg border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={formData.db_name}
                      onChange={(e) => setFormData({ ...formData, db_name: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Usuario</label>
                    <input 
                      type="text" 
                      placeholder="postgres" 
                      className="w-full p-2 bg-gray-800 rounded-lg border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={formData.db_user}
                      onChange={(e) => setFormData({ ...formData, db_user: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Contraseña</label>
                    <input 
                      type="password" 
                      placeholder="••••••••" 
                      className="w-full p-2 bg-gray-800 rounded-lg border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={formData.db_password}
                      onChange={(e) => setFormData({ ...formData, db_password: e.target.value })}
                      required
                    />
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-indigo-900/20 border border-indigo-800/50 rounded-xl">
                <ShieldCheck size={18} className="text-indigo-400 mt-0.5 shrink-0"/>
                <p className="text-xs text-indigo-300">
                  Al confirmar, OmniCore-AI vinculará tu agente y ejecutará automáticamente los <strong>Blueprints SQL</strong> para crear todas las tablas necesarias en tu base de datos.
                </p>
              </div>

              <button 
                type="submit" 
                disabled={creating}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 rounded-lg font-bold transition-all flex items-center justify-center gap-2"
              >
                {creating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Desplegando Infraestructura...
                  </>
                ) : 'Lanzar Agente Zero-to-Hero'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectDashboard;
