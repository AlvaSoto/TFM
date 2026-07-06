import React from 'react';
import { Sparkles } from 'lucide-react';

/**
 * Informe del asistente IA: tarjeta limpia con acento, sin efectos de demo.
 * El contenido (diagnóstico / impacto económico / consejo) es el protagonista.
 */
const AIAdvisorCard = ({ report }) => {
  if (!report) return null;

  // Formateo simple de **negritas** de markdown
  const formatText = (text) =>
    text.split('\n').map((line, i) => (
      <p key={i} className="mb-2.5 last:mb-0 leading-relaxed">
        {line.split('**').map((part, j) =>
          j % 2 === 1
            ? <strong key={j} className="font-semibold text-slate-900">{part}</strong>
            : part
        )}
      </p>
    ));

  return (
    <div className="card p-6 h-full border-l-4" style={{ borderLeftColor: '#2a78d6' }}>
      <div className="flex items-center justify-between mb-4 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 bg-blue-50 rounded-lg">
            <Sparkles className="w-4.5 h-4.5 text-blue-600" size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Asistente inteligente</h2>
            <p className="text-xs text-slate-500">Informe generado a partir del análisis del contador</p>
          </div>
        </div>
      </div>

      <div className="text-sm text-slate-600">
        {formatText(report)}
      </div>
    </div>
  );
};

export default AIAdvisorCard;
