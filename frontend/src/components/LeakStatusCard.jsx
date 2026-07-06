import React from 'react';
import { AlertTriangle, CheckCircle, Droplets, CalendarRange } from 'lucide-react';

/**
 * Estado del contador para el ciudadano: diagnóstico + datos reales
 * (periodo afectado y pérdida estimada desde los datos del hogar).
 */
const LeakStatusCard = ({ leakData, lossEstimate }) => {
  const isLeak = leakData.is_leak_detected;
  const period = leakData.leak_period || {};

  return (
    <div
      className="card p-6 h-full border-l-4"
      style={{ borderLeftColor: isLeak ? '#d03b3b' : '#0ca30c' }}
    >
      <div className="flex items-center gap-3 mb-4">
        <div className={`p-2.5 rounded-xl ${isLeak ? 'bg-red-50' : 'bg-emerald-50'}`}>
          {isLeak
            ? <AlertTriangle size={24} className="text-red-600" strokeWidth={2.25} />
            : <CheckCircle size={24} className="text-emerald-600" strokeWidth={2.25} />}
        </div>
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Estado del contador
          </p>
          <h2 className={`text-lg font-bold ${isLeak ? 'text-red-700' : 'text-emerald-700'}`}>
            {isLeak ? 'Fuga detectada' : 'Todo en orden'}
          </h2>
        </div>
      </div>

      {isLeak ? (
        <div className="space-y-3">
          {period.start && (
            <div className="flex items-start gap-2 text-sm text-slate-600">
              <CalendarRange size={16} className="text-slate-400 mt-0.5 shrink-0" />
              <span>
                Periodo afectado: <strong className="text-slate-800">{period.start}</strong>
                {period.end && period.end !== period.start && <> → <strong className="text-slate-800">{period.end}</strong></>}
              </span>
            </div>
          )}
          {lossEstimate?.liters > 0 && (
            <div className="flex items-start gap-2 text-sm text-slate-600">
              <Droplets size={16} className="text-slate-400 mt-0.5 shrink-0" />
              <span>
                Pérdida estimada: <strong className="text-slate-800">
                  {Math.round(lossEstimate.liters).toLocaleString('es-ES')} L
                </strong>
                {lossEstimate.eur > 0 && <> (≈ <strong className="text-slate-800">{lossEstimate.eur} €</strong>)</>}
              </span>
            </div>
          )}
          <p className="text-xs text-slate-500 leading-relaxed pt-2 border-t border-slate-100">
            Consumo sostenido incompatible con el patrón habitual del hogar.
            Recomendamos revisar cisternas, riego automático y llaves de paso.
          </p>
        </div>
      ) : (
        <p className="text-sm text-slate-600 leading-relaxed">
          El consumo se mantiene dentro del patrón habitual del hogar.
          Te avisaremos al momento si detectamos cualquier anomalía.
        </p>
      )}
    </div>
  );
};

export default LeakStatusCard;
