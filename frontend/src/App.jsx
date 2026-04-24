import { useState, useEffect } from 'react';
import { getHouseholds, analyzeHousehold, getRegions } from './services/api';
import { Droplets, Activity, CheckCircle, Sparkles, Github, Linkedin, Mail } from 'lucide-react';

// --- COMPONENTES ---
import LandingPage from './components/LandingPage';
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
  const [showLanding, setShowLanding] = useState(true);

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
    <>
      {showLanding ? (
        <LandingPage onEnter={() => setShowLanding(false)} />
      ) : (
        <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-4 md:p-8">
          <div className="max-w-7xl mx-auto space-y-8">
        
        {/* --- HEADER PROFESIONAL --- */}
        <header className="glass rounded-2xl p-6 shadow-lg mb-2">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex items-center gap-4">
              <button 
                onClick={() => setShowLanding(true)}
                className="cursor-pointer hover:scale-105 transition-transform"
                title="Volver al inicio"
              >
                <div className="relative">
                  <div className="absolute inset-0 bg-blue-500 rounded-2xl blur-md opacity-30 animate-pulse-glow"></div>
                  <div className="relative bg-gradient-to-br from-blue-500 to-blue-700 text-white p-3 rounded-2xl shadow-xl">
                    <Droplets size={32} strokeWidth={2.5} />
                  </div>
                </div>
              </button>
              <div>
                <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-blue-600 via-blue-700 to-blue-900 bg-clip-text text-transparent">
                  Smart Water Monitor
                </h1>
                <p className="text-slate-600 mt-1 text-sm font-medium">
                  Plataforma de Gestión Hídrica con IA · Detección Predictiva de Fugas
                </p>
              </div>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex items-center gap-2 px-4 py-2.5 bg-emerald-50 rounded-xl border border-emerald-200 text-sm font-semibold text-emerald-700">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                Sistema Activo
              </div>
              <div className="hidden sm:flex items-center gap-2 px-4 py-2.5 bg-blue-50 rounded-xl border border-blue-200 text-sm font-semibold text-blue-700">
                <Activity size={16} />
                v2.0 Pro
              </div>
            </div>
          </div>
        </header>

        {/* --- BARRA DE CONTROL MEJORADA --- */}
        <div className="glass rounded-2xl p-6 shadow-lg animate-slide-in">
          <div className="flex flex-col lg:flex-row gap-5 items-end lg:items-center">
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
              className="group relative w-full lg:w-auto bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-10 py-4 rounded-xl font-bold transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95 flex items-center justify-center min-w-[180px] overflow-hidden"
            >
              <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-10 transition-opacity"></div>
              <span className="relative z-10 flex items-center gap-2">
                {loading ? (
                  <>
                    <LoadingSpinner />
                    Analizando...
                  </>
                ) : (
                  <>
                    <Activity size={20} />
                    Generar Informe
                  </>
                )}
              </span>
            </button>
          </div>
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
        
        {/* --- ESTADO VACÍO MEJORADO --- */}
        {!data && !loading && !error && (
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-50 via-blue-50/30 to-slate-50 border-2 border-dashed border-slate-200 p-16 animate-fade-in">
            <div className="absolute top-10 right-10 w-32 h-32 bg-blue-200 rounded-full blur-3xl opacity-20"></div>
            <div className="absolute bottom-10 left-10 w-40 h-40 bg-purple-200 rounded-full blur-3xl opacity-20"></div>
            
            <div className="relative flex flex-col items-center justify-center text-center max-w-lg mx-auto">
              <div className="mb-6 relative">
                <div className="absolute inset-0 bg-blue-400 rounded-full blur-xl opacity-20 animate-pulse"></div>
                <div className="relative bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-2xl shadow-2xl">
                  <Droplets size={48} strokeWidth={2} />
                </div>
              </div>
              
              <h3 className="text-2xl font-bold text-slate-800 mb-3">
                Panel de Diagnóstico Listo
              </h3>
              <p className="text-slate-600 text-lg mb-6 leading-relaxed">
                Selecciona un hogar y región para iniciar el análisis inteligente de consumo hídrico
              </p>
              
              <div className="grid grid-cols-3 gap-6 w-full mt-4">
                <div className="flex flex-col items-center gap-2">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Activity className="text-blue-600" size={24} />
                  </div>
                  <span className="text-xs font-semibold text-slate-600">Detección IA</span>
                </div>
                <div className="flex flex-col items-center gap-2">
                  <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                    <CheckCircle className="text-emerald-600" size={24} />
                  </div>
                  <span className="text-xs font-semibold text-slate-600">Análisis 24/7</span>
                </div>
                <div className="flex flex-col items-center gap-2">
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                    <Sparkles className="text-purple-600" size={24} />
                  </div>
                  <span className="text-xs font-semibold text-slate-600">Insights IA</span>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>

      {/* === FOOTER PROFESIONAL === */}
      <footer className="max-w-7xl mx-auto mt-16 pb-8">
        <div className="glass rounded-2xl p-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-6">
            {/* Columna 1: Branding */}
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="bg-gradient-to-br from-blue-500 to-blue-700 text-white p-2 rounded-lg">
                  <Droplets size={20} />
                </div>
                <h3 className="font-bold text-lg text-slate-800">Smart Water Monitor</h3>
              </div>
              <p className="text-sm text-slate-600 leading-relaxed">
                Plataforma inteligente de monitorización y detección de fugas hídricas mediante IA.
              </p>
              <div className="flex gap-2 pt-2">
                <a href="https://github.com/AlvaSoto/TFM" target="_blank" rel="noopener noreferrer" className="p-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors">
                  <Github size={18} className="text-slate-600" />
                </a>
                <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="p-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors">
                  <Linkedin size={18} className="text-slate-600" />
                </a>
                <a href="mailto:contact@example.com" className="p-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors">
                  <Mail size={18} className="text-slate-600" />
                </a>
              </div>
            </div>

            {/* Columna 2: Características */}
            <div className="space-y-3">
              <h4 className="font-semibold text-slate-800 text-sm uppercase tracking-wide">Tecnología</h4>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                  Detección con LSTM Autoencoder
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                  Análisis predictivo con IA
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                  Reportes GPT-4o
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                  Monitorización en tiempo real
                </li>
              </ul>
            </div>

            {/* Columna 3: Información */}
            <div className="space-y-3">
              <h4 className="font-semibold text-slate-800 text-sm uppercase tracking-wide">Proyecto</h4>
              <ul className="space-y-2 text-sm text-slate-600">
                <li>Trabajo Final de Máster</li>
                <li>Universidad Europea</li>
                <li>Máster en IA</li>
                <li className="pt-2">
                  <span className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-semibold">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    v2.0 Pro · 2026
                  </span>
                </li>
              </ul>
            </div>
          </div>

          {/* Copyright */}
          <div className="pt-6 border-t border-slate-200 text-center">
            <p className="text-sm text-slate-500">
              © 2026 Smart Water Monitor. Desarrollado con{' '}
              <span className="text-red-500">♥</span> por{' '}
              <span className="font-semibold text-slate-700">Álvaro Soto Álvarez</span>
            </p>
          </div>
        </div>
      </footer>
      </div>
      )}
    </>
  );
}

export default App;