import { useState, useEffect } from 'react';
import { getHouseholds, analyzeHousehold, getRegions } from './services/api';
import { Droplets, Activity } from 'lucide-react';

// --- COMPONENTES ---
import AlertMessage from './components/AlertMessage';
import HouseholdSelector from './components/HouseholdSelector';
import RegionSelector from './components/RegionSelector';
import LoadingSpinner from './components/LoadingSpinner';

// Tarjetas de Estado y Análisis
import AIAdvisorCard from './components/AIAdvisorCard';
import LeakStatusCard from './components/LeakStatusCard'; // <--- NUEVO
import DailyTrendCard from './components/DailyTrendCard'; // <--- NUEVO
import CostEstimateCard from './components/CostEstimateCard';
import BillHistory from './components/BillHistory';       // <--- NUEVO

// Gráficas
import ConsumptionChart from './components/ConsumptionChart';
import HourlyPatternsChart from './components/HourlyPatternsChart';

function App() {
  // Estados de Datos
  const [households, setHouseholds] = useState([]);
  const [regions, setRegions] = useState([]);
  
  // Estados de Selección
  const [selectedHouse, setSelectedHouse] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('Promedio Nacional');
  
  // Estados de UI
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 1. Carga Inicial (Casas y Regiones)
  useEffect(() => {
    const initData = async () => {
      try {
        const [h, r] = await Promise.all([getHouseholds(), getRegions()]);
        setHouseholds(h);
        setRegions(r);
      } catch (e) { 
        console.error(e);
        setError("Error de conexión con el servidor. Verifica que el backend está corriendo."); 
      }
    };
    initData();
  }, []);

  // 2. Manejador del botón "Analizar"
  const handleAnalyze = async () => {
    if (!selectedHouse) return;
    
    setLoading(true);
    setData(null);
    setError(null);

    try {
      const res = await analyzeHousehold(selectedHouse, selectedRegion);
      setData(res);
    } catch (e) { 
      console.error(e);
      setError("No se pudo analizar el hogar seleccionado. Inténtalo de nuevo."); 
    } finally { 
      setLoading(false); 
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* --- HEADER --- */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 border-b border-slate-200">
          <div>
            <h1 className="text-3xl md:text-4xl font-extrabold flex items-center gap-3 text-slate-800">
              <div className="bg-blue-600 text-white p-2.5 rounded-xl shadow-lg shadow-blue-200">
                <Droplets size={28} />
              </div>
              Smart Water Monitor
            </h1>
            <p className="text-slate-500 mt-2 text-lg font-medium ml-1">
              Plataforma de Gestión Hídrica Inteligente
            </p>
          </div>
          
          <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-white rounded-full border border-slate-200 text-sm text-slate-500 font-medium">
            <Activity size={16} className="text-green-500" />
            Sistema Operativo v2.0
          </div>
        </header>

        {/* --- BARRA DE CONTROL --- */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 flex flex-col lg:flex-row gap-5 items-end lg:items-center">
          <div className="flex flex-col md:flex-row gap-4 w-full lg:flex-grow">
            <HouseholdSelector 
              households={households} 
              selectedHouse={selectedHouse} 
              setSelectedHouse={setSelectedHouse} 
              disabled={loading}
            />
            <RegionSelector 
              regions={regions} 
              selectedRegion={selectedRegion} 
              setSelectedRegion={setSelectedRegion} 
              disabled={loading}
            />
          </div>
          
          <button 
            onClick={handleAnalyze}
            disabled={!selectedHouse || loading}
            className="w-full lg:w-auto bg-blue-600 hover:bg-blue-700 text-white px-8 py-3.5 rounded-xl font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-blue-100 flex items-center justify-center min-w-[160px]"
          >
            {loading ? <LoadingSpinner /> : 'Generar Informe'}
          </button>
        </div>

        {/* --- MENSAJES DE ERROR --- */}
        {error && <AlertMessage message={error} type="error" />}

        {/* --- DASHBOARD PRINCIPAL --- */}
        {data && (
          <div className="animate-fade-in space-y-6">
            
            {/* FILA 1: INFORMACIÓN CRÍTICA (Estado + IA) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1 h-full">
                {/* AVISO VISUAL DE FUGA */}
                <LeakStatusCard leakData={data.leak_detection} />
              </div>
              <div className="lg:col-span-2 h-full">
                {/* CONSEJO DE GPT-4o */}
                <AIAdvisorCard report={data.ai_assistant.report} />
              </div>
            </div>

            {/* FILA 2: METRICAS FINANCIERAS Y OPERATIVAS */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Tarjeta 1: Hoy vs Ayer */}
              <DailyTrendCard dailyData={data.consumption_analytics.daily_status} />
              
              {/* Tarjeta 2: Factura Estimada Mes Actual */}
              <CostEstimateCard 
                kpis={data.consumption_analytics.financial_kpis} 
                region={data.region_applied} 
              />
              
              {/* Tarjeta 3: Tabla Histórica (Ocupa espacio para verse bien) */}
              <div className="md:col-span-2 lg:col-span-1">
                <BillHistory 
                  history={data.consumption_analytics.bills_history} 
                  currentRegion={data.region_applied}
                />
              </div>
            </div>

            {/* FILA 3: ANÁLISIS VISUAL (GRÁFICAS) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Gráfica Grande (Evolución) */}
              <div className="lg:col-span-2">
                <ConsumptionChart 
                  data={data.consumption_analytics.charts.daily_consumption}
                  communityAvg={data.consumption_analytics.community_comparison.community_daily_avg}
                  anomalousDays={data.leak_detection.anomalous_days} 
                />
              </div>
              
              {/* Gráfica Pequeña (Patrones Horarios) */}
              <div className="lg:col-span-1">
                <HourlyPatternsChart 
                  data={data.consumption_analytics.charts.hourly_patterns}
                />
              </div>
            </div>

          </div>
        )}
        
        {/* --- ESTADO VACÍO --- */}
        {!data && !loading && !error && (
          <div className="flex flex-col items-center justify-center py-24 text-slate-400 border-2 border-dashed border-slate-200 rounded-3xl bg-slate-50/50">
            <div className="bg-white p-4 rounded-full shadow-sm mb-4">
              <Activity size={40} className="text-slate-300" />
            </div>
            <p className="text-xl font-medium text-slate-600">El panel de control está listo.</p>
            <p className="text-sm">Selecciona un hogar y una región para comenzar el diagnóstico.</p>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;