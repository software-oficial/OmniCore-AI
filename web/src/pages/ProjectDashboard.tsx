import { useEffect, useState } from 'react';
import api from '../services/api';
import { Plus, Key, BarChart2, X } from 'lucide-react';

interface Project {
  id: string;
  name: string;
}

const ProjectDashboard = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [creating, setCreating] = useState(false);

  const fetchProjects = async () => {
    try {
      const response = await api.get('/agent/projects');
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post('/agent/projects/create', { name: projectName });
      setProjectName('');
      setIsModalOpen(false);
      await fetchProjects();
    } catch (error) {
      console.error('Error creating project:', error);
      alert('Error creating project');
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
          <Plus size={18}/> Nuevo Proyecto
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
              No tienes proyectos activos. ¡Crea el primero!
            </div>
          )}
        </div>
      )}

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-700 w-full max-w-md rounded-2xl p-6 shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">Crear Nuevo Proyecto</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-white">
                <X size={24}/>
              </button>
            </div>
            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Nombre del Proyecto</label>
                <input 
                  autoFocus
                  type="text" 
                  placeholder="Ej: Mi Tienda Online" 
                  className="w-full p-3 bg-gray-800 rounded-lg border border-gray-700 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  required
                />
              </div>
              <button 
                type="submit" 
                disabled={creating}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 rounded-lg font-bold transition-colors"
              >
                {creating ? 'Creando...' : 'Confirmar Creación'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectDashboard;
