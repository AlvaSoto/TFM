import { useState, useEffect } from 'react';
import { getHouseholds, analyzeHousehold, getRegions } from './services/api';
import { Droplets, LayoutDashboard, User, ShieldCheck, MapPin } from 'lucide-react';

import FleetOverview from './components/FleetOverview';
import HouseholdView from './components/HouseholdView';
import SystemPanel from './components/SystemPanel';

const NAV = [
  { id: 'fleet', label: 'Operaciones', icon: LayoutDashboard, hint: 'Flota y alertas' },
  { id: 'household', label: 'Vista Hogar', icon: User, hint: 'Detalle ciudadano' },
  { id: 'system', label: 'Sistema', icon: ShieldCheck, hint: 'Modelo y trazabilidad' },
];

const VIEW_TITLES = {
  fleet: { title: 'Panel de Operaciones', sub: 'Priorización de intervenciones sobre la flota de contadores' },
  household: { title: 'Vista Hogar', sub: 'Lo que ve el ciudadano en la app white-label' },
  system: { title: 'Sistema', sub: 'Modelo desplegado, datos y métricas de la última evaluación' },
};

function App() {
  // Navegación
  const [view, setView] = useState('fleet');

  // Datos maestros
  const [households, setHouseholds] = useState([]);
  const [regions, setRegions] = useState([]);

  // Selección
  const [selectedHouse, setSelectedHouse] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('Promedio Nacional');

  // Estado del análisis de hogar
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const init = async () => {
      try {
        const [h, r] = await Promise.all([getHouseholds(), getRegions()]);
        setHouseholds(h);
        setRegions(r);
      } catch (e) {
        console.error(e);
        setError('Error de conexión con el servidor. Verifica que el backend está corriendo.');
      }
    };
    init();
  }, []);

  const handleAnalyze = async (houseId = selectedHouse) => {
    if (!houseId) return;
    setLoading(true);
    setData(null);
    setError(null);
    try {
      const res = await analyzeHousehold(houseId, selectedRegion);
      setData(res);
    } catch (e) {
      console.error(e);
      setError('No se pudo analizar el hogar seleccionado. Inténtalo de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  // Drill-down desde la cola de alertas del operador
  const handleSelectFromFleet = (houseId) => {
    setSelectedHouse(houseId);
    setView('household');
    handleAnalyze(houseId);
  };

  const { title, sub } = VIEW_TITLES[view];

  return (
    <div className="min-h-screen flex">

      {/* ============ SIDEBAR ============ */}
      <aside
        className="w-60 shrink-0 flex flex-col text-slate-300"
        style={{ background: 'var(--sidebar)' }}
      >
        {/* Marca (white-label: aquí va el logo de la gestora) */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
          <div className="bg-gradient-to-br from-sky-500 to-blue-700 text-white p-2 rounded-xl">
            <Droplets size={20} strokeWidth={2.5} />
          </div>
          <div className="min-w-0">
            <div className="font-bold text-white leading-tight">Smart Water</div>
            <div className="text-[11px] text-slate-400 leading-tight">Consola de la gestora</div>
          </div>
        </div>

        {/* Navegación */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ id, label, icon: Icon, hint }) => {
            const active = view === id;
            return (
              <button
                key={id}
                onClick={() => setView(id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors ${
                  active ? 'text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
                style={{ background: active ? 'var(--sidebar-active)' : 'transparent' }}
                onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'var(--sidebar-hover)'; }}
                onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent'; }}
              >
                <Icon size={18} className={active ? 'text-sky-400' : ''} />
                <span className="flex-1">
                  <span className="block text-sm font-semibold">{label}</span>
                  <span className="block text-[11px] opacity-60">{hint}</span>
                </span>
              </button>
            );
          })}
        </nav>

        {/* Pie */}
        <div className="px-5 py-4 border-t border-white/10 text-[11px] text-slate-500 space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            Sistema operativo
          </div>
          <div>Smart Water Monitor · v2.1</div>
        </div>
      </aside>

      {/* ============ CONTENIDO ============ */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Topbar */}
        <header className="bg-white border-b border-slate-200 px-6 py-4 flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-slate-900">{title}</h1>
            <p className="text-sm text-slate-500 truncate">{sub}</p>
          </div>

          {/* Selector de región global (afecta a la valoración en €) */}
          <label className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2">
            <MapPin size={15} className="text-slate-400" />
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Tarifa</span>
            <select
              className="bg-transparent text-sm font-medium text-slate-700 focus:outline-none cursor-pointer"
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
            >
              {regions.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </label>
        </header>

        {/* Vista activa */}
        <main className="flex-1 overflow-y-auto p-6">
          {view === 'fleet' && (
            <FleetOverview region={selectedRegion} onSelectHousehold={handleSelectFromFleet} />
          )}

          {view === 'household' && (
            <HouseholdView
              households={households}
              selectedHouse={selectedHouse}
              setSelectedHouse={setSelectedHouse}
              data={data}
              loading={loading}
              error={error}
              onAnalyze={() => handleAnalyze()}
              onBackToFleet={() => setView('fleet')}
            />
          )}

          {view === 'system' && <SystemPanel />}
        </main>
      </div>
    </div>
  );
}

export default App;
