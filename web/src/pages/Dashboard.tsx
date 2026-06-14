import { useEffect, useState } from 'react';
import api from '../services/api';
import { Plus, Key, BarChart2 } from 'lucide-react';

interface Project { id: string; name: string; }

const Dashboard = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get('/agent/projects');
        setProjects(response.data);
      } catch (err) {
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      <header className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Panel de Control</h1>
      </header>

      {/* Stats Section (Simulated) */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
          <p className="text-gray-400 text-xs uppercase">Uso API (Total)</p>
          <p className="text-xl font-bold">1,240 calls</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
          <p className="text-gray-400 text-xs uppercase">Proyectos</p>
          <p className="text-xl font-bold">{projects.length}</p>
        </div>
      </div>

      {/* Projects List */}
      <section>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Tus Proyectos</h2>
          <button className="text-indigo-400"><Plus size={24}/></button>
        </div>
        <div className="space-y-3">
          {loading ? <p>Cargando...</p> : projects.map(p => (
            <div key={p.id} className="bg-gray-800 p-4 rounded-xl border border-gray-700 flex justify-between items-center">
              <div>
                <p className="font-medium">{p.name}</p>
                <p className="text-xs text-gray-500 font-mono">{p.id.slice(0, 8)}...</p>
              </div>
              <div className="flex gap-2">
                <button className="p-2 text-indigo-400 bg-indigo-900/30 rounded-lg"><Key size={18}/></button>
                <button className="p-2 text-emerald-400 bg-emerald-900/30 rounded-lg"><BarChart2 size={18}/></button>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default Dashboard;
