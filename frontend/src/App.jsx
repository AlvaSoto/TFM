import { useState, useEffect } from 'react';
import { getHouseholds, analyzeHousehold } from './services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { AlertTriangle, CheckCircle, Droplets, Activity } from 'lucide-react';

function App() {
  const [households, setHouseholds] = useState([]);
  const [selectedHouse, setSelectedHouse] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 1. Cargar lista de casas al iniciar
  useEffect(() => {
    getHouseholds()
      .then(setHouseholds)
      .catch(err => console.error("Error cargando casas:", err));
  }, []);

  // 2. Función para analizar la casa seleccionada
  const handleAnalyze = async () => {
    if (!selectedHouse) return;
    setLoading(true);
    setError(null);
    setData(null);

    try {
      const result = await analyzeHousehold(selectedHouse);
      // Transformar datos para la gráfica (Recharts necesita un array de objetos)
      const chartData = result.analysis_result.mse_values.map((mse, index) => ({
        index: index,
        mse: mse,
        threshold: result.analysis_result.threshold_used // Línea del umbral
      }));
      setData({ ...result, chartData });
    } catch (err) {
      setError("Error al analizar la casa. Asegúrate de que el Backend está corriendo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      {/* HEADER */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
          <Droplets className="text-blue-500" />
          Smart Water Leak Detector
        </h1>
        <p className="text-gray-500 mt-2">Sistema de detección de anomalías basado en LSTM Autoencoder</p>
      </header>

      {/* CONTROLES */}
      <div className="bg-white p-6 rounded-xl shadow-md flex gap-4 items-center mb-8">
        <select 
          className="border p-2 rounded-lg flex-grow max-w-md bg-gray-50"
          value={selectedHouse}
          onChange={(e) => setSelectedHouse(e.target.value)}
        >
          <option value="">-- Selecciona un Hogar --</option>
          {households.map(h => (
            <option key={h} value={h}>{h}</option>
          ))}
        </select>
        
        <button 
          onClick={handleAnalyze}
          disabled={!selectedHouse || loading}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
        >
          {loading ? 'Analizando...' : 'Analizar Consumo'}
        </button>
      </div>

      {/* ERROR MESSAGE */}
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-8" role="alert">
          <p>{error}</p>
        </div>
      )}

      {/* RESULTADOS */}
      {data && (
        <div className="space-y-8 animate-fade-in">
          
          {/* TARJETAS DE ESTADO */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Tarjeta 1: Estado Final */}
            <div className={`p-6 rounded-xl shadow-md border-l-8 ${data.analysis_result.is_leak_detected ? 'bg-red-50 border-red-500' : 'bg-green-50 border-green-500'}`}>
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium text-gray-500 uppercase">Diagnóstico</p>
                  <h3 className={`text-2xl font-bold ${data.analysis_result.is_leak_detected ? 'text-red-700' : 'text-green-700'}`}> 
                    {data.analysis_result.is_leak_detected ? 'FUGA DETECTADA' : 'SISTEMA NORMAL'}
                  </h3>
                </div>
                {data.analysis_result.is_leak_detected ? <AlertTriangle size={40} className="text-red-500"/> : <CheckCircle size={40} className="text-green-500"/>}
              </div>
            </div>

            {/* Tarjeta 2: Anomalías */}
            <div className="bg-white p-6 rounded-xl shadow-md border-l-8 border-blue-500">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium text-gray-500 uppercase">Anomalías / Total</p>
                  <h3 className="text-2xl font-bold text-gray-800">
                    {data.analysis_result.anomalies_detected} <span className="text-sm text-gray-400">/ {data.analysis_result.total_sequences_analyzed}</span>
                  </h3>
                </div>
                <Activity size={40} className="text-blue-500"/>
              </div>
            </div>

            {/* Tarjeta 3: Porcentaje */}
            <div className="bg-white p-6 rounded-xl shadow-md border-l-8 border-purple-500">
              <div>
                <p className="text-sm font-medium text-gray-500 uppercase">% Tiempo Anómalo</p>
                <h3 className="text-2xl font-bold text-gray-800">
                  {data.analysis_result.percentage_anomalies}%
                </h3>
              </div>
            </div>
          </div>

          {/* GRÁFICA */}
          <div className="bg-white p-6 rounded-xl shadow-md">
            <h3 className="text-lg font-bold text-gray-700 mb-4">Error de Reconstrucción (MSE) vs Umbral</h3>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.chartData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="index" label={{ value: 'Secuencias (Tiempo)', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'MSE (Error)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend verticalAlign="top" height={36}/>
                  {/* Línea del Error (Azul) */}
                  <Line 
                    type="monotone" 
                    dataKey="mse" 
                    stroke="#3b82f6" 
                    strokeWidth={2} 
                    dot={false} 
                    name="Error de Reconstrucción" 
                  />
                  {/* Línea del Umbral (Roja discontinua) */}
                  <ReferenceLine 
                    y={data.analysis_result.threshold_used} 
                    label="Umbral de Alarma" 
                    stroke="red" 
                    strokeDasharray="5 5" 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-sm text-gray-500 mt-4 text-center">
              Si la línea azul supera la línea roja discontinua, se considera una anomalía en ese intervalo de tiempo.
            </p>
          </div>

        </div>
      )}
    </div>
  );
}

export default App;