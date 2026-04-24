import React from 'react';
import { AlertTriangle, CheckCircle, Shield } from 'lucide-react';

const LeakStatusCard = ({ leakData }) => {
  const isLeak = leakData.is_leak_detected;
  
  return (
    <div className={`relative overflow-hidden p-6 rounded-2xl card-shadow-lg transition-all duration-300 hover:scale-[1.02] border-l-4 ${
      isLeak 
        ? "bg-gradient-to-br from-red-50 to-red-100/50 border-red-500" 
        : "bg-gradient-to-br from-emerald-50 to-emerald-100/50 border-emerald-500"
    }`}>
      {/* Efecto de fondo decorativo */}
      <div className={`absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl opacity-20 ${
        isLeak ? "bg-red-400" : "bg-emerald-400"
      }`}></div>
      
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Shield size={16} className={isLeak ? "text-red-600" : "text-emerald-600"} />
              <h3 className="text-xs font-bold uppercase tracking-wider opacity-70">
                {isLeak ? "Alerta Crítica" : "Estado del Sistema"}
              </h3>
            </div>
            
            <div className="flex items-center gap-3 mb-3">
              <div className={`p-3 rounded-xl ${isLeak ? "bg-red-100" : "bg-emerald-100"}`}>
                {isLeak 
                  ? <AlertTriangle size={28} className="text-red-600" strokeWidth={2.5} /> 
                  : <CheckCircle size={28} className="text-emerald-600" strokeWidth={2.5} />
                }
              </div>
              <div>
                <h2 className={`text-xl font-bold ${isLeak ? "text-red-700" : "text-emerald-700"}`}>
                  {isLeak ? "FUGA DETECTADA" : "OPERACIÓN NORMAL"}
                </h2>
              </div>
            </div>
            
            {isLeak ? (
              <div className="space-y-2">
                <p className="text-sm text-red-700 font-semibold">
                  ⚠️ {leakData.anomalies_detected} anomalías detectadas
                </p>
                <p className="text-xs text-red-600 leading-relaxed">
                  El sistema ha identificado patrones anormales en el consumo. Se recomienda inspección inmediata.
                </p>
              </div>
            ) : (
              <p className="text-sm text-emerald-700 font-medium">
                ✓ Consumo dentro de parámetros normales. Sistema funcionando correctamente.
              </p>
            )}
          </div>
        </div>
        
        {/* Indicador visual de severidad */}
        <div className="mt-4 pt-4 border-t border-slate-200/50">
          <div className="flex items-center justify-between text-xs">
            <span className={`font-semibold ${isLeak ? "text-red-600" : "text-emerald-600"}`}>
              Nivel de Confianza
            </span>
            <span className={`font-bold ${isLeak ? "text-red-700" : "text-emerald-700"}`}>
              {isLeak ? "Alta Certeza" : "100%"}
            </span>
          </div>
          <div className="mt-2 h-2 bg-white rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${
                isLeak ? "bg-gradient-to-r from-red-500 to-red-600 w-[85%]" : "bg-gradient-to-r from-emerald-500 to-emerald-600 w-full"
              }`}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeakStatusCard;