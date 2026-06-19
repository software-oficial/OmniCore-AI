import React from 'react';

const PaymentPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Pasarela de Pagos</h1>
      <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-xl">
        <p className="text-slate-400">Gestión de transacciones, cupones y métodos de pago.</p>
        <div className="grid grid-cols-3 gap-4 mt-6">
          <div className="p-4 bg-slate-900 rounded-lg border border-slate-700 text-center">
            <p className="text-xs text-slate-500 uppercase">Ventas Hoy</p>
            <p className="text-2xl font-bold text-green-400">$0.00</p>
          </div>
          <div className="p-4 bg-slate-900 rounded-lg border border-slate-700 text-center">
            <p className="text-xs text-slate-500 uppercase">Transacciones</p>
            <p className="text-2xl font-bold text-cyan-400">0</p>
          </div>
          <div className="p-4 bg-slate-900 rounded-lg border border-slate-700 text-center">
            <p className="text-xs text-slate-500 uppercase">Errores</p>
            <p className="text-2xl font-bold text-red-400">0</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentPage;
