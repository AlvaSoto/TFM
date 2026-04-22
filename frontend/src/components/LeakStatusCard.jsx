import React from 'react';
import { AlertTriangle, CheckCircle } from 'lucide-react';

const LeakStatusCard = ({ leakData }) => {
  const isLeak = leakData.is_leak_detected;
  
  return (
    <div className={`p-6 rounded-2xl shadow-sm border-l-8 transition-all ${
      isLeak ? "bg-red-50 border-red-500" : "bg-emerald-50 border-emerald-500"
    }`}>
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider mb-2 opacity-70">
            {isLeak ? "Alerta de Sistema" : "Estado del Sistema"}
          </h3>
          <div className="flex items-center gap-3">
            {isLeak ? <AlertTriangle size={32} className="text-red-600" /> : <CheckCircle size={32} className="text-emerald-600" />}
            <div>
              <span className={`text-2xl font-extrabold ${isLeak ? "text-red-700" : "text-emerald-700"}`}>
                {isLeak ? "FUGA DETECTADA" : "FUNCIONAMIENTO NORMAL"}
              </span>
              {isLeak && (
                <p className="text-sm text-red-600 mt-1 font-medium">
                  Se han detectado {leakData.anomalies_detected} anomalías en el patrón de consumo.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeakStatusCard;