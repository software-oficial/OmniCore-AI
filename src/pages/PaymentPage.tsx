import React from 'react';

const commands = [
  { key: 'GEN_PAYMENT_QR', desc: 'Genera códigos QR de pago dinámicos para cobro rápido.', color: 'var(--accent-payments)' },
  { key: 'GEN_PAYMENT_LINK', desc: 'Crea enlaces de pago personalizados para enviar por chat.', color: 'var(--accent-payments)' },
  { key: 'MULTI_CRED_MNG', desc: 'Gestiona múltiples credenciales de Mercado Pago y otros.', color: 'var(--accent-payments)' },
  { key: 'GET_ACCOUNTS', desc: 'Lista pasarelas y credenciales activas del sistema.', color: 'var(--accent-payments)' },
  { key: 'GET_SUMMARY', desc: 'Resumen de transacciones y volumen de ventas por cuenta.', color: 'var(--accent-payments)' },
  { key: 'REFUND_TX', desc: 'Procesa reembolsos de transacciones específicas.', color: 'var(--accent-payments)' },
];

const PaymentPage: React.FC = () => {
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
            className="command-card" 
            style={{ '--accent-color': cmd.color } as any}
            onClick={() => alert(`Ejecutando comando: ${cmd.key}`)}
          >
            <div>
              <span className="command-key">{cmd.key}</span>
              <p className="command-desc">{cmd.desc}</p>
            </div>
            <div className="btn-run">Ejecutar Comando</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PaymentPage;
