import React, { useState } from 'react';
import api from '../services/api';

const commands = [
  { key: 'GEN_PAYMENT_QR', desc: 'Genera códigos QR de pago dinámicos para cobro rápido.', endpoint: '/business/credentials', method: 'POST', color: 'var(--accent-payments)' },
  { key: 'GEN_PAYMENT_LINK', desc: 'Crea enlaces de pago personalizados para enviar por chat.', endpoint: '/business/credentials', method: 'POST', color: 'var(--accent-payments)' },
  { key: 'MULTI_CRED_MNG', desc: 'Gestiona múltiples credenciales de Mercado Pago y otros.', endpoint: '/business/credentials', method: 'POST', color: 'var(--accent-payments)' },
  { key: 'GET_ACCOUNTS', desc: 'Lista pasarelas y credenciales activas del sistema.', endpoint: '/business/credentials', method: 'GET', color: 'var(--accent-payments)' },
  { key: 'GET_SUMMARY', desc: 'Resumen de transacciones y volumen de ventas por cuenta.', endpoint: '/audit', method: 'GET', color: 'var(--accent-payments)' },
  { key: 'REFUND_TX', desc: 'Procesa reembolsos de transacciones específicas.', endpoint: '/business/credentials', method: 'PATCH', color: 'var(--accent-payments)' },
];

const PaymentPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{success: boolean, message: string} | null>(null);

  const executeCommand = async (cmd: typeof commands[0]) => {
    setLoading(true);
    setResult(null);
    try {
      const response = await api[cmd.method.toLowerCase() as 'get' | 'post' | 'patch'](cmd.endpoint, cmd.method === 'GET' ? undefined : {});
      setResult({ success: true, message: response.data.message || 'Comando ejecutado exitosamente' });
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.response?.data?.message || 'Error al ejecutar el comando';
      setResult({ success: false, message: msg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="omnicore-container">
      <div className="omnicore-header">
        <h1>Pasarela de Pagos</h1>
        <p className="text-slate-400">Gestión de Cobros, QR y Credenciales Multi-Cuenta</p>
      </div>

      <div className="command-grid">
        {commands.map(cmd => (
          <div 
            key={cmd.key} 
            className={`command-card ${loading ? 'opacity-50 pointer-events-none' : ''}`} 
            style={{ '--accent-color': cmd.color } as any}
            onClick={() => executeCommand(cmd)}
          >
            <div>
              <span className="command-key">{cmd.key}</span>
              <p className="command-desc">{cmd.desc}</p>
            </div>
            <div className={`btn-run ${loading ? 'animate-pulse' : ''}`}>
              {loading ? 'Ejecutando...' : 'Ejecutar Comando'}
            </div>
          </div>
        ))}
      </div>

      {result && (
        <div className={`fixed bottom-8 right-8 p-4 rounded-xl shadow-2xl border animate-in slide-in-from-bottom-4 duration-300 ${
          result.success ? 'bg-green-900/80 border-green-500 text-green-100' : 'bg-red-900/80 border-red-500 text-red-100'
        }`}>
          <p className="text-sm font-medium">{result.message}</p>
        </div>
      )}
    </div>
  );
};

export default PaymentPage;
