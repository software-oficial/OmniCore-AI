import { BookOpen, Database, Server, ShieldCheck, ArrowRight, Terminal } from 'lucide-react';

const DocumentationPage = () => {
  const apiSections = [
    {
      category: "🔑 Autenticación y Gestión",
      endpoints: [
        { path: "/api/auth/login", method: "POST", purpose: "Obtiene el token JWT de sesión para gestionar la cuenta." },
        { path: "/api/auth/tokens/create", method: "POST", purpose: "Genera un token de API persistente para un Agente de IA." },
        { path: "/api/agent/me", method: "GET", purpose: "Verifica la identidad y datos del agente autenticado." },
        { path: "/api/agent/manifest", method: "GET", purpose: "Obtiene la ontología del sistema y el flujo de onboarding." },
        { path: "/api/agent/guides", method: "GET", purpose: "Manual detallado de configuración de infraestructura Local Linux." },
      ]
    },
    {
      category: "🏗️ Gestión de Proyectos (Infraestructura)",
      endpoints: [
        { path: "/api/agent/onboard", method: "POST", purpose: "FLUJO ZERO-TO-HERO: Registra agente, vincula DB local y despliega esquema automáticamente." },
        { path: "/api/agent/projects", method: "GET", purpose: "Lista todos los proyectos vinculados al agente." },
        { path: "/api/agent/projects/create", method: "POST", purpose: "Vincula una base de datos externa al sistema manualmente." },
      ]
    },
    {
      category: "🚀 Orquestador de Negocio (Gateway)",
      endpoints: [
        { path: "/api/gateway/execute", method: "POST", purpose: "Endpoint Maestro. Ejecuta cualquier comando de negocio inyectando la sesión de la DB local." },
        { path: "/api/discovery/commands", method: "GET", purpose: "Lista todos los comandos disponibles y sus esquemas de parámetros." },
        { path: "/api/discovery/aliases", method: "GET", purpose: "Diccionario de alias soportados para comandos." },
      ]
    },
    {
      category: "🩺 Salud del Sistema",
      endpoints: [
        { path: "/health", method: "GET", purpose: "Verifica el estado de conexión con la API, Redis y el Core Registry." },
      ]
    }
  ];

  return (
    <div className="space-y-10 p-6 max-w-5xl mx-auto">
      {/* Hero Section */}
      <header className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-white flex items-center justify-center gap-3">
          <BookOpen size={36} className="text-indigo-400"/> Centro de Documentación
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Todo lo que necesitas saber para montar tu servidor local y conectar tu negocio al orquestador OmniCore-AI.
        </p>
      </header>

      {/* BYODB Alert Box */}
      <section className="bg-indigo-900/20 border border-indigo-500/50 p-6 rounded-2xl space-y-4">
        <div className="flex items-center gap-3 text-indigo-400 font-bold text-xl">
          <Database size={24}/> Despliegue Local Linux (BYODB)
        </div>
        <p className="text-gray-300 leading-relaxed">
          OmniCore-AI es un orquestador stateless. Para operar, debes instalar <span className="text-white font-mono">PostgreSQL</span> en tu servidor Linux. 
          Tú tienes el control total de tus datos; OmniCore-AI se conecta a tu servidor local para ejecutar la lógica de negocio.
        </p>
        
        <div className="bg-indigo-950/60 p-5 rounded-xl border border-indigo-400/30 space-y-4 mt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-indigo-600 p-2 rounded-lg text-white"><Download size={20}/></div>
              <div>
                <h4 className="text-white font-bold">OmniCore SDK (Python)</h4>
                <p className="text-xs text-gray-400">Puente obligatorio para la ejecución local de comandos.</p>
              </div>
            </div>
            <a 
              href="/api/sdk/download" 
              className="bg-indigo-500 hover:bg-indigo-400 text-white px-4 py-2 rounded-lg text-sm font-bold transition-colors flex items-center gap-2"
            >
              <Download size={16}/> Descargar SDK
            </a>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="bg-indigo-950/50 p-4 rounded-xl border border-indigo-500/30 flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg text-white"><Server size={16}/></div>
            <span className="text-sm text-gray-300">1. Instalar PostgreSQL en Linux</span>
          </div>
          <div className="bg-indigo-950/50 p-4 rounded-xl border border-indigo-500/30 flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg text-white"><Terminal size={16}/></div>
            <span className="text-sm text-gray-300">2. Auto-Onboarding vía API</span>
          </div>
          <div className="bg-indigo-950/50 p-4 rounded-xl border border-indigo-500/30 flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg text-white"><ShieldCheck size={16}/></div>
            <span className="text-sm text-gray-300">3. Verificar Comandos</span>
          </div>
        </div>
      </section>

      {/* Endpoints List */}
      <div className="space-y-8">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <ArrowRight size={24} className="text-indigo-400"/> Catálogo de Endpoints
        </h2>
        
        {apiSections.map((section, idx) => (
          <div key={idx} className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-400 uppercase tracking-wider">{section.category}</h3>
            <div className="grid gap-3">
              {section.endpoints.map((ep, epIdx) => (
                <div key={epIdx} className="bg-gray-800 border border-gray-700 p-4 rounded-xl flex items-center justify-between group hover:border-indigo-500/50 transition-all">
                  <div className="flex items-center gap-4">
                    <span className={`text-[10px] font-bold px-2 py-1 rounded w-16 text-center ${
                      ep.method === 'POST' ? 'bg-emerald-900/30 text-emerald-400' : 'bg-blue-900/30 text-blue-400'
                    }`}>
                      {ep.method}
                    </span>
                    <div>
                      <code className={`text-sm font-mono ${ep.path === '/api/agent/onboard' ? 'text-yellow-400 font-bold' : 'text-indigo-300'}`}>{ep.path}</code>
                      <p className="text-sm text-gray-400 mt-1">{ep.purpose}</p>
                    </div>
                  </div>
                  {ep.path === '/api/agent/onboard' && (
                    <span className="bg-yellow-500/20 text-yellow-500 text-[10px] font-bold px-2 py-1 rounded uppercase">Recomendado</span>
                  )}
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity text-xs text-gray-500 italic">
                    Ver en Explorador $ightarrow$
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DocumentationPage;
