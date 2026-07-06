import { useState, useEffect, useCallback, useMemo } from 'react';
import { getFleetOverview, scoreFleet } from '../services/api';
import {
  AlertTriangle, Droplets, Euro, Home, RefreshCw, ChevronRight,
  CheckCircle, Search,
} from 'lucide-react';
import NetworkTrendChart from './NetworkTrendChart';

/**
 * Vista OPERACIONES: el panel de la gestora.
 * KPIs de flota + tendencias de red + cola de intervención con filtros.
 */

function KpiTile({ icon: Icon, label, value, sub, accent }) {
  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        <Icon size={15} style={accent ? { color: accent } : undefined} />
        {label}
      </div>
      <div className="text-3xl font-bold mt-2 text-slate-900">{value}</div>
      {sub && <div className="text-xs mt-1 text-slate-500">{sub}</div>}
    </div>
  );
}

function LevelBadge({ level, mlDetected }) {
  if (level === 'CONFIRMADA') {
    return (
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold text-white"
        style={{ background: '#d03b3b' }}
        title="Caudal nocturno continuo: la firma física de una fuga (precisión 1.0 en evaluación)"
      >
        <AlertTriangle size={12} /> CONFIRMADA
      </span>
    );
  }
  if (level === 'SOSPECHA') {
    return (
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold text-amber-900"
        style={{ background: '#fab219' }}
        title="Patrón anómalo detectado por el modelo IA, sin confirmación física nocturna"
      >
        <AlertTriangle size={12} /> SOSPECHA
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold text-emerald-800 bg-emerald-100">
      <CheckCircle size={12} /> OK
    </span>
  );
}

const FILTERS = [
  { id: 'ALL', label: 'Todas' },
  { id: 'CONFIRMADA', label: 'Confirmadas' },
  { id: 'SOSPECHA', label: 'Sospechas' },
  { id: 'OK', label: 'OK' },
];

export default function FleetOverview({ region, onSelectHousehold }) {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scoring, setScoring] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('ALL');
  const [query, setQuery] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setOverview(await getFleetOverview(region));
    } catch (e) {
      console.error(e);
      setError('No se pudo cargar la vista de flota. Verifica que el backend está corriendo.');
    } finally {
      setLoading(false);
    }
  }, [region]);

  useEffect(() => { load(); }, [load]);

  const handleScoreMore = async () => {
    setScoring(true);
    try {
      setOverview(await scoreFleet(10, region));
    } catch (e) {
      console.error(e);
      setError('Error al analizar hogares pendientes.');
    } finally {
      setScoring(false);
    }
  };

  const filtered = useMemo(() => {
    if (!overview) return [];
    let rows = overview.households;
    if (filter !== 'ALL') rows = rows.filter((h) => h.alert_level === filter);
    if (query.trim()) {
      const q = query.trim().toLowerCase();
      rows = rows.filter((h) => h.household_id.toLowerCase().includes(q));
    }
    return rows;
  }, [overview, filter, query]);

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card p-5">
              <div className="skeleton h-3 w-24 mb-3"></div>
              <div className="skeleton h-8 w-20"></div>
            </div>
          ))}
        </div>
        <div className="card p-6"><div className="skeleton h-64 w-full"></div></div>
      </div>
    );
  }

  if (error) {
    return <div className="card p-8 text-red-600 font-medium">{error}</div>;
  }

  const { kpis } = overview;
  const fmt = (n) => Number(n).toLocaleString('es-ES');

  return (
    <div className="space-y-6 animate-fade-in">

      {/* --- KPIs --- */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiTile
          icon={Home}
          label="Contadores"
          value={`${kpis.households_scored}/${kpis.households_total}`}
          sub={kpis.households_pending > 0 ? `${kpis.households_pending} pendientes de análisis` : 'Flota completa analizada'}
          accent="#2a78d6"
        />
        <KpiTile
          icon={AlertTriangle}
          label="Alertas activas"
          value={kpis.active_alerts}
          sub={`${kpis.confirmed_alerts ?? 0} confirmadas (caudal nocturno) · ${kpis.suspected_alerts ?? 0} sospechas (IA)`}
          accent="#d03b3b"
        />
        <KpiTile
          icon={Droplets}
          label="Agua perdida est."
          value={`${fmt(Math.round(kpis.estimated_loss_l / 1000))} m³`}
          sub="Exceso sobre línea base en días anómalos"
          accent="#2a78d6"
        />
        <KpiTile
          icon={Euro}
          label="Impacto económico"
          value={`${fmt(kpis.estimated_loss_eur)} €`}
          sub={`Tarifa ${kpis.region}: ${kpis.price_per_m3} €/m³`}
          accent="#0ca30c"
        />
      </div>

      {/* --- Tendencias de red --- */}
      <NetworkTrendChart />

      {/* --- Cola de intervención --- */}
      <div className="card p-6">
        <div className="flex flex-col lg:flex-row lg:items-center gap-3 mb-5">
          <div className="flex-1">
            <h2 className="text-base font-bold text-slate-900">Cola de intervención</h2>
            <p className="text-xs text-slate-500">
              {filtered.length} de {overview.households.length} hogares · priorizados por pérdida estimada
            </p>
          </div>

          {/* Filtros por nivel */}
          <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
            {FILTERS.map((f) => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                  filter === f.id ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Búsqueda */}
          <label className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
            <Search size={14} className="text-slate-400" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar contador..."
              className="bg-transparent text-sm focus:outline-none w-36"
            />
          </label>

          {kpis.households_pending > 0 && (
            <button
              onClick={handleScoreMore}
              disabled={scoring}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50"
            >
              <RefreshCw size={15} className={scoring ? 'animate-spin' : ''} />
              {scoring ? 'Analizando...' : 'Analizar 10 pendientes'}
            </button>
          )}
        </div>

        {filtered.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-sm">
            {overview.households.length === 0
              ? 'Aún no hay hogares analizados. Pulsa «Analizar pendientes» o ejecuta python -m app.services.fleet.'
              : 'Ningún hogar coincide con el filtro actual.'}
          </div>
        ) : (
          <div className="overflow-x-auto -mx-2 px-2">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wide text-slate-500 border-b border-slate-200">
                  <th className="py-2.5 pr-4 font-semibold">Contador</th>
                  <th className="py-2.5 pr-4 font-semibold">Perfil</th>
                  <th className="py-2.5 pr-4 font-semibold">Estado</th>
                  <th className="py-2.5 pr-4 font-semibold text-right">Anomalías</th>
                  <th className="py-2.5 pr-4 font-semibold text-right">Días</th>
                  <th className="py-2.5 pr-4 font-semibold text-right">Pérdida</th>
                  <th className="py-2.5 pr-4 font-semibold text-right">Coste</th>
                  <th className="py-2.5"></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((h) => (
                  <tr
                    key={h.household_id}
                    onClick={() => onSelectHousehold(h.household_id)}
                    className="border-b border-slate-100 hover:bg-blue-50/60 cursor-pointer transition-colors group"
                  >
                    <td className="py-2.5 pr-4 font-medium text-slate-800 whitespace-nowrap">{h.household_id}</td>
                    <td className="py-2.5 pr-4 text-slate-500 whitespace-nowrap">
                      {h.profile ? `${h.profile.label}${h.profile.people ? ` · ${h.profile.people}p` : ''}` : '—'}
                    </td>
                    <td className="py-2.5 pr-4">
                      <LevelBadge level={h.alert_level} mlDetected={h.is_leak_detected} />
                    </td>
                    <td className="py-2.5 pr-4 text-right text-slate-600 tabular">{h.percentage_anomalies}%</td>
                    <td className="py-2.5 pr-4 text-right text-slate-600 tabular">{h.anomalous_days_count}</td>
                    <td className="py-2.5 pr-4 text-right font-semibold text-slate-800 tabular">
                      {h.estimated_loss_l > 0 ? `${fmt(Math.round(h.estimated_loss_l))} L` : '—'}
                    </td>
                    <td className="py-2.5 pr-4 text-right font-semibold text-slate-800 tabular">
                      {h.estimated_loss_eur > 0 ? `${fmt(h.estimated_loss_eur)} €` : '—'}
                    </td>
                    <td className="py-2.5 text-right text-slate-300 group-hover:text-blue-600 transition-colors">
                      <ChevronRight size={16} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
