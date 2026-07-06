import { ArrowLeft, Home, Activity, AlertTriangle, CheckCircle, Moon } from 'lucide-react';
import HouseholdSelector from './HouseholdSelector';
import LoadingSpinner from './LoadingSpinner';
import AlertMessage from './AlertMessage';

import AIAdvisorCard from './AIAdvisorCard';
import LeakStatusCard from './LeakStatusCard';
import DailyTrendCard from './DailyTrendCard';
import CostEstimateCard from './CostEstimateCard';
import BillHistory from './BillHistory';
import ConsumptionChart from './ConsumptionChart';
import HourlyPatternsChart from './HourlyPatternsChart';

/**
 * Vista HOGAR: lo que vería el ciudadano en la app white-label,
 * con contexto extra para el operador (nivel de ensemble, perfil).
 */
export default function HouseholdView({
  households, selectedHouse, setSelectedHouse,
  data, loading, error, onAnalyze, onBackToFleet,
}) {
  const ensemble = data?.ensemble;
  const profile = data?.profile;

  return (
    <div className="space-y-6 animate-fade-in">

      {/* --- Cabecera: breadcrumb + selector --- */}
      <div className="card p-5">
        <div className="flex flex-col lg:flex-row lg:items-end gap-4">
          <button
            onClick={onBackToFleet}
            className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-blue-700 transition-colors self-start"
          >
            <ArrowLeft size={16} /> Volver a Operaciones
          </button>

          <div className="flex-1 flex flex-col md:flex-row gap-3 md:items-end">
            <div className="flex-1 max-w-md">
              <HouseholdSelector
                households={households}
                selectedHouse={selectedHouse}
                setSelectedHouse={setSelectedHouse}
                disabled={loading}
              />
            </div>
            <button
              onClick={onAnalyze}
              disabled={!selectedHouse || loading}
              className="flex items-center justify-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <><LoadingSpinner /> Analizando...</> : <><Activity size={16} /> Analizar</>}
            </button>
          </div>
        </div>

        {/* Contexto del hogar analizado */}
        {data && (
          <div className="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t border-slate-100">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 rounded-full text-xs font-medium text-slate-600">
              <Home size={12} />
              {profile ? `${profile.label}${profile.people ? ` · ${profile.people} personas` : ''}` : data.household_id}
            </span>

            {ensemble && (
              ensemble.alert_level === 'CONFIRMADA' ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold text-white" style={{ background: '#d03b3b' }}>
                  <AlertTriangle size={12} /> FUGA CONFIRMADA (IA + caudal nocturno)
                </span>
              ) : ensemble.alert_level === 'SOSPECHA' ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold text-amber-900" style={{ background: '#fab219' }}>
                  <AlertTriangle size={12} /> SOSPECHA — un solo detector
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-100 rounded-full text-xs font-bold text-emerald-800">
                  <CheckCircle size={12} /> Sin indicios de fuga
                </span>
              )
            )}

            {ensemble?.mnf_alert && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 rounded-full text-xs font-medium text-slate-600"
                    title="Noches en las que el caudal nunca bajó del suelo mínimo">
                <Moon size={12} />
                {ensemble.mnf_days_count} noches con caudal continuo (suelo máx. {ensemble.max_night_floor_l} L/15min)
              </span>
            )}
          </div>
        )}
      </div>

      {error && <AlertMessage message={error} type="error" />}

      {/* --- Dashboard del ciudadano --- */}
      {data && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1 h-full">
              <LeakStatusCard leakData={data.leak_detection} lossEstimate={data.loss_estimate} />
            </div>
            <div className="lg:col-span-2 h-full">
              <AIAdvisorCard report={data.ai_assistant.report} />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <DailyTrendCard dailyData={data.consumption_analytics.daily_status} />
            <CostEstimateCard
              kpis={data.consumption_analytics.financial_kpis}
              region={data.region_applied}
            />
            <div className="md:col-span-2 lg:col-span-1">
              <BillHistory
                history={data.consumption_analytics.bills_history}
                currentRegion={data.region_applied}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <ConsumptionChart
                data={data.consumption_analytics.charts.daily_consumption}
                communityAvg={data.consumption_analytics.community_comparison.community_daily_avg}
                anomalousDays={data.leak_detection.anomalous_days}
              />
            </div>
            <div className="lg:col-span-1">
              <HourlyPatternsChart data={data.consumption_analytics.charts.hourly_patterns} />
            </div>
          </div>
        </>
      )}

      {/* --- Estado vacío --- */}
      {!data && !loading && !error && (
        <div className="card p-16 text-center">
          <div className="inline-flex p-4 bg-blue-50 rounded-2xl text-blue-600 mb-4">
            <Home size={32} />
          </div>
          <h3 className="text-lg font-bold text-slate-800 mb-2">Selecciona un hogar</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Elige un contador y pulsa «Analizar», o entra desde la cola de intervención
            de Operaciones para ver el detalle de una alerta.
          </p>
        </div>
      )}
    </div>
  );
}
