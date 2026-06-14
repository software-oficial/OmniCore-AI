import { useEffect, useState } from 'react';
import api from '../services/api';
import { Play, Info, Terminal, ChevronRight, Search } from 'lucide-react';

interface Command {
  command: string;
  description: string;
  params: Record<string, string>;
  is_system: boolean;
}

interface DiscoveryData {
  agent_id: string;
  mode: string;
  total_commands: number;
  commands: Command[];
}

const ApiExplorer = () => {
  const [data, setData] = useState<DiscoveryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCommand, setSelectedCommand] = useState<Command | null>(null);
  const [params, setParams] = useState<Record<string, string>>({});
  const [response, setResponse] = useState<any>(null);
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    const fetchCommands = async () => {
      try {
        const res = await api.get('/discovery/commands');
        setData(res.data);
      } catch (err) {
        console.error('Error fetching commands:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchCommands();
  }, []);

  const handleParamChange = (key: string, value: string) => {
    setParams(prev => ({ ...prev, [key]: value }));
  };

  const executeCommand = async () => {
    setExecuting(true);
    setResponse(null);
    try {
      const res = await api.post('/gateway/execute', {
        command: selectedCommand?.command,
        params: params
      });
      setResponse(res.data);
    } catch (err: any) {
      setResponse({ success: false, message: err.response?.data?.message || 'Execution error' });
    } finally {
      setExecuting(false);
    }
  };

  const filteredCommands = data?.commands.filter(cmd => 
    cmd.command.toLowerCase().includes(searchQuery.toLowerCase()) || 
    cmd.description.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  if (loading) return <div className="p-8 text-center text-gray-400">Cargando comandos...</div>;

  return (
    <div className="flex h-full overflow-hidden">
      {/* Sidebar: Command List */}
      <div className="w-1/3 border-r border-gray-700 bg-gray-900 flex flex-col">
        <div className="p-4 border-b border-gray-700 space-y-4">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Terminal size={20} className="text-indigo-400"/> Explorador API
          </h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16}/>
            <input 
              type="text" 
              placeholder="Buscar comando..." 
              className="w-full pl-10 pr-4 py-2 bg-gray-800 rounded-lg border border-gray-700 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {filteredCommands.map(cmd => (
            <button 
              key={cmd.command}
              onClick={() => {
                setSelectedCommand(cmd);
                setParams({});
                setResponse(null);
              }}
              className={`w-full text-left p-3 rounded-lg transition-colors flex items-center justify-between group ${
                selectedCommand?.command === cmd.command 
                ? 'bg-indigo-600 text-white' 
                : 'hover:bg-gray-800 text-gray-400 hover:text-gray-200'
              }`}
            >
              <span className="text-sm font-mono">{cmd.command}</span>
              <ChevronRight size={14} className={`transition-transform ${selectedCommand?.command === cmd.command ? 'rotate-90' : 'group-hover:translate-x-1'}`}/>
            </button>
          ))}
        </div>
      </div>

      {/* Main: Execution Panel */}
      <div className="flex-1 overflow-y-auto bg-gray-950 p-6 space-y-6">
        {!selectedCommand ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
            <Terminal size={48} className="opacity-20"/>
            <p>Selecciona un comando para empezar a probar</p>
          </div>
        ) : (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <section className="bg-gray-900 p-6 rounded-2xl border border-gray-700 space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-2xl font-bold font-mono text-indigo-400">{selectedCommand.command}</h3>
                  <p className="text-gray-400 mt-1">{selectedCommand.description}</p>
                </div>
                <div className="flex gap-2">
                  <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${selectedCommand.is_system ? 'bg-red-900/30 text-red-400' : 'bg-emerald-900/30 text-emerald-400'}`}>
                    {selectedCommand.is_system ? 'System' : 'Business'}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                {Object.entries(selectedCommand.params).map(([key, type]) => (
                  <div key={key} className="space-y-1">
                    <label className="text-xs font-medium text-gray-500 uppercase">{key} ({type})</label>
                    <input 
                      type="text" 
                      className="w-full p-2 bg-gray-800 rounded-lg border border-gray-700 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
                      value={params[key] || ''}
                      onChange={(e) => handleParamChange(key, e.target.value)}
                      placeholder={`Valor para ${key}...`}
                    />
                  </div>
                ))}
                {Object.keys(selectedCommand.params).length === 0 && (
                  <p className="text-sm text-gray-500 italic">Este comando no requiere parámetros.</p>
                )}
              </div>

              <button 
                onClick={executeCommand}
                disabled={executing}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 rounded-xl font-bold flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
              >
                <Play size={18}/> {executing ? 'Ejecutando...' : 'Ejecutar Comando'}
              </button>
            </section>

            {response && (
              <section className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-400">
                  <Info size={16}/> Respuesta del Servidor
                </div>
                <div className="bg-black p-4 rounded-2xl border border-gray-700 font-mono text-sm overflow-x-auto">
                  <pre className={`whitespace-pre-wrap ${response.success ? 'text-emerald-400' : 'text-red-400'}`}>
                    {JSON.stringify(response, null, 2)}
                  </pre>
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ApiExplorer;
