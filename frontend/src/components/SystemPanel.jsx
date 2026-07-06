import { useState, useEffect } from 'react';
import { getSystemInfo } from '../services/api';
import { Cpu, Database, GitMerge, Gauge, FlaskConical } from 'lucide-react';

/**
 * Vista SISTEMA: trazabilidad de lo desplegado.
 * Qué modelo corre, con qué umbral y de dónde sale, sobre qué datos,
 * y las métricas de la última evaluación honesta.
 * La pantalla que responde a la due diligence técnica de un cliente.
 */

function InfoRow({ label, value, mono = false }) {
  return (
    <div className="flex justify-between gap-4 py-2 border-b border-slate-100 last:border-0">
      <span className="text-sm text-slate-500">{label}</span>
      <span className={`text-sm font-medium text-slate-800 text-right ${mono ? 'font-mono text-xs' : ''}`}>
        {value}
      </span>
    </div>
  );
}

function SectionCard({ icon: Icon, title, children }) {
  return (
    <div className="card p-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 bg-slate-100 rounded-lg text-slate-600"><Icon size={16} /></div>
        <h2 className="text-base font-bold text-slate-900">{title}</h2>
      </div>
      {children}
    </div>
  );
}

export default function SystemPanel() {
  const [info, setInfo] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getSystemInfo().then(setInfo).catch(() => setError('No se pudo cargar la información del sistema.'));
  }, []);

  if (error) return <div className="card p-8 text-red-600 font-medium">{error}</div>;

  if (!info) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card p-6">
            <div className="skeleton h-4 w-40 mb-4"></div>
            <div className="skeleton h-24 w-full"></div>
          </div>
        ))}
      </div>
    );
  }

  const evalMetrics = info.last_evaluation?.day_level_metrics;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in">

      <SectionCard icon={Cpu} title="Modelo desplegado">
        <InfoRow label="Arquitectura" value={info.model.architecture} />
        <InfoRow label="Umbral de detección" value={info.model.threshold} mono />
        <InfoRow label="Origen del umbral" value={info.model.threshold_source} />
        <InfoRow label="Artefacto" value={info.model.path} mono />
      </SectionCard>

      <SectionCard icon={GitMerge} title="Ensemble de detección">
        {info.ensemble.components.map((c) => (
          <div key={c} className="flex items-center gap-2 py-1.5 text-sm text-slate-700">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>{c}
          </div>
        ))}
        <div className="mt-3 pt-3 border-t border-slate-100 space-y-1">
          {Object.entries(info.ensemble.levels).map(([level, desc]) => (
            <div key={level} className="flex gap-2 text-xs">
              <span className="font-bold text-slate-700 w-24">{level}</span>
              <span className="text-slate-500">{desc}</span>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard icon={Database} title="Dataset activo">
        <InfoRow label="Fichero" value={info.dataset.file} mono />
        <InfoRow label="Lecturas" value={Number(info.dataset.rows).toLocaleString('es-ES')} />
        <InfoRow label="Contadores" value={info.dataset.households} />
        <InfoRow label="Periodo" value={`${info.dataset.date_from} → ${info.dataset.date_to}`} />
        <InfoRow label="Resolución" value={info.dataset.resolution} />
        <InfoRow label="Flota puntuada" value={`${info.fleet.scored}/${info.fleet.total}`} />
      </SectionCard>

      <SectionCard icon={FlaskConical} title="Última evaluación (nivel día, ground truth)">
        {evalMetrics ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wide text-slate-500 border-b border-slate-200">
                  <th className="py-2 pr-3 font-semibold">Detector</th>
                  <th className="py-2 pr-3 font-semibold text-right">Precision</th>
                  <th className="py-2 pr-3 font-semibold text-right">Recall</th>
                  <th className="py-2 font-semibold text-right">F1</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(evalMetrics).map(([name, m]) => (
                  <tr key={name} className="border-b border-slate-100 last:border-0">
                    <td className="py-2 pr-3 font-medium text-slate-700">{name}</td>
                    <td className="py-2 pr-3 text-right tabular text-slate-600">{m.precision}</td>
                    <td className="py-2 pr-3 text-right tabular text-slate-600">{m.recall}</td>
                    <td className="py-2 text-right tabular font-semibold text-slate-800">{m.f1}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-[11px] text-slate-400 mt-3">
              Evaluado sobre {info.last_evaluation.households_evaluated} hogares contra el etiquetado
              del simulador (ground truth). «AND» respalda las alertas CONFIRMADAS.
            </p>
          </div>
        ) : (
          <p className="text-sm text-slate-500">
            Sin evaluación registrada. Ejecuta <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs">python -m app.ml.evaluate_ensemble</code>.
          </p>
        )}
      </SectionCard>

      <SectionCard icon={Gauge} title="Entorno">
        <InfoRow label="TensorFlow" value={info.versions.tensorflow} mono />
        <InfoRow label="scikit-learn" value={info.versions.scikit_learn} mono />
      </SectionCard>
    </div>
  );
}
