import React, { useState } from 'react';
import api from '../services/api';

interface RowPreview {
  row: number;
  original: Record<string, any>;
  mapped: Record<string, any>;
  error?: string;
}

interface PreviewResponse {
  status: 'success' | 'needs_mapping' | 'error';
  data?: RowPreview[];
  message: string;
  headers?: string[];
  mapping_used?: Record<string, string>;
}

const InventoryImportPage: React.FC = () => {
  const [fileData, setFileData] = useState<Record<string, any>[]>([]);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [customMapping, setCustomMapping] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      const rows = text.split('
').filter(row => row.trim());
      const headers = rows[0].split(',').map(h => h.trim());
      
      const data = rows.slice(1).map(row => {
        const values = row.split(',');
        return headers.reduce((acc, header, i) => {
          acc[header] = values[i]?.trim() || '';
          return acc;
        }, {} as Record<string, any>);
      });

      setFileData(data);
      requestPreview(data);
    };
    reader.readAsText(file);
  };

  const requestPreview = async (data: Record<string, any>[]) => {
    try {
      setLoading(true);
      const response = await api.post('/import/preview', { 
        raw_data: data, 
        custom_mapping: customMapping 
      });
      setPreview(response.data.data);
      if (response.data.data.mapping_used) {
        setCustomMapping(response.data.data.mapping_used);
      }
    } catch (error) {
      alert('Error generating preview');
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteImport = async () => {
    if (!preview || !preview.mapping_used) return;
    
    try {
      setIsImporting(true);
      const response = await api.post('/import/execute', { 
        raw_data: fileData, 
        mapping: preview.mapping_used 
      });
      alert(`Import success: ${response.data.data.success} products added.`);
      setFileData([]);
      setPreview(null);
    } catch (error) {
      alert('Import failed');
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-800">Carga Masiva de Inventario</h1>
        <p className="text-sm text-gray-500">Sube un archivo CSV para importar tus productos rápidamente.</p>
      </div>

      {!preview && (
        <div className="flex flex-col items-center justify-center p-12 border-2 border-dashed border-gray-300 rounded-3xl bg-gray-50 hover:bg-gray-100 transition cursor-pointer relative">
          <input 
            type="file" 
            accept=".csv" 
            onChange={handleFileUpload}
            className="absolute inset-0 opacity-0 cursor-pointer"
          />
          <div className="text-center">
            <div className="text-5xl mb-4">📄</div>
            <p className="text-lg font-medium text-gray-700">Haz clic o arrastra tu archivo CSV aquí</p>
            <p className="text-sm text-gray-400 mt-1">Solo archivos .csv compatibles</p>
          </div>
        </div>
      )}

      {loading && <div className="text-center p-8">Analizando datos y sugiriendo mapeo...</div>}

      {preview && (
        <div className="space-y-6 animate-in fade-in duration-500">
          <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl flex justify-between items-center">
            <div>
              <p className="text-blue-800 font-medium">Mapeo Detectado Automáticamente</p>
              <p className="text-xs text-blue-600">Revisa que las columnas coincidan con los campos internos.</p>
            </div>
            <button 
              onClick={() => requestPreview(fileData)}
              className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
            >
              Actualizar Preview
            </button>
          </div>

          <div className="bg-white shadow-md rounded-xl overflow-hidden border border-gray-200">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead className="bg-gray-50 text-gray-600 uppercase text-xs font-semibold">
                  <tr>
                    <th className="px-6 py-3 border-b">Fila</th>
                    <th className="px-6 py-3 border-b">Datos Originales</th>
                    <th className="px-6 py-3 border-b">Resultado Mapeado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {preview.data?.slice(0, 10).map((row) => (
                    <tr key={row.row} className="hover:bg-gray-50 transition">
                      <td className="px-6 py-4 text-sm text-gray-400">{row.row}</td>
                      <td className="px-6 py-4">
                        <pre className="text-[10px] bg-gray-100 p-2 rounded max-w-xs overflow-hidden text-ellipsis">
                          {JSON.stringify(row.original)}
                        </pre>
                      </td>
                      <td className="px-6 py-4">
                        {row.error ? (
                          <span className="text-xs text-red-500 font-medium">{row.error}</span>
                        ) : (
                          <pre className="text-[10px] bg-green-50 p-2 rounded max-w-xs overflow-hidden text-green-700">
                            {JSON.stringify(row.mapped, null, 2)}
                          </pre>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-4 bg-gray-50 text-center text-xs text-gray-500">
              Mostrando las primeras 10 filas de {preview.data?.length} procesadas.
            </div>
          </div>

          <div className="flex justify-between items-center">
            <button 
              onClick={() => setPreview(null)}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition"
            >
              Cancelar y Volver
            </button>
            <button 
              onClick={handleExecuteImport}
              disabled={isImporting}
              className={`px-6 py-2 bg-green-600 text-white rounded-lg font-bold shadow-lg transition ${isImporting ? 'opacity-50 cursor-not-allowed' : 'hover:bg-green-700'}`}
            >
              {isImporting ? 'Importando...' : 'Confirmar e Importar Productos'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default InventoryImportPage;
