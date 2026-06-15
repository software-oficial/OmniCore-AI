import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { Mail, Lock, LogIn, ArrowRight } from 'lucide-react';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await api.post('/auth/login', { email, password });
      localStorage.setItem('omnicore_token', response.data.data.user_id);
      navigate('/projects');
    } catch (err: unknown) {
      const errorData = err as Record<string, unknown>;
      const response = errorData.response as Record<string, unknown>;
      const data = response?.data as Record<string, unknown>;
      setError((data?.detail as string) || 'Error de autenticación');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 p-4">
      <div className="w-full max-w-md bg-gray-900 border border-gray-800 rounded-3xl p-8 shadow-2xl space-y-8">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl shadow-lg shadow-indigo-500/20 mb-4">
            <LogIn size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Bienvenido</h1>
          <p className="text-gray-400 text-sm">Accede al centro de mando de OmniCore-AI</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs font-medium text-gray-400 uppercase ml-1">Correo Electrónico</label>
            <div className="relative group">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-indigo-400 transition-colors" size={20} />
              <input 
                type="email" 
                placeholder="nombre@empresa.com" 
                className="w-full pl-11 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-medium text-gray-400 uppercase ml-1">Contraseña</label>
            <div className="relative group">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-indigo-400 transition-colors" size={20} />
              <input 
                type="password" 
                placeholder="••••••••" 
                className="w-full pl-11 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-900/20 border border-red-800 rounded-xl text-red-400 text-xs text-center">
              {error}
            </div>
          )}

          <button 
            type="submit" 
            disabled={loading}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 text-white font-bold rounded-xl shadow-lg shadow-indigo-500/20 transition-all active:scale-95 flex items-center justify-center gap-2"
          >
            {loading ? 'Autenticando...' : 'Iniciar Sesión'}
            {!loading && <ArrowRight size={20} />}
          </button>
        </form>

        <div className="text-center">
          <p className="text-gray-500 text-sm">
            ¿No tienes cuenta?{' '}
            <Link to="/register" className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
              Regístrate gratis
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
