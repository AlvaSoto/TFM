import React from 'react';
import { AlertTriangle, CheckCircle, Droplets, DollarSign, Activity } from 'lucide-react';

// Estilo base para las tarjetas
const Card = ({ title, value, subtext, icon: Icon, colorClass, borderClass }) => (
  <div className={`p-6 rounded-xl shadow-sm border-l-4 bg-white hover:shadow-md transition-shadow ${borderClass}`}>
    <div className="flex justify-between items-start">
      <div>
        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">{title}</p>
        <h3 className={`text-2xl font-bold ${colorClass}`}>{value}</h3>
        {subtext && <p className="text-sm text-gray-500 mt-1">{subtext}</p>}
      </div>
      <div className={`p-3 rounded-full ${colorClass.replace('text-', 'bg-').replace('700', '100')} ${colorClass.replace('text-', 'text-').replace('700', '500')}`}>
        <Icon size={24} />
      </div>
    </div>
  </div>
);

const AnalysisResult = ({ data }) => {
  const { leak_detection, consumption_analytics } = data;
  const isLeak = leak_detection.is_leak_detected;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {/* 1. Diagnóstico de Fuga */}
      <Card 
        title="Diagnóstico del Sistema"
        value={isLeak ? 'FUGA DETECTADA' : 'SISTEMA NORMAL'}
        subtext={isLeak 
          ? `Detectadas ${leak_detection.anomalies_detected} anomalías (${leak_detection.percentage_anomalies}% del tiempo)`
          : 'No se detectan anomalías significativas.'
        }
        icon={isLeak ? AlertTriangle : CheckCircle}
        colorClass={isLeak ? 'text-red-700' : 'text-green-700'}
        borderClass={isLeak ? 'border-red-500' : 'border-green-500'}
      />

      {/* 2. KPIs de Consumo */}
      <Card 
        title="Consumo Diario Promedio"
        value={`${consumption_analytics.financial_kpis.daily_average_l} L`}
        subtext={`Total acumulado: ${consumption_analytics.financial_kpis.total_consumption_l} L`}
        icon={Droplets}
        colorClass="text-blue-700"
        borderClass="border-blue-500"
      />

      {/* 3. Factura y Comunidad */}
      <Card 
        title={`Factura Estimada (${data.region_applied})`} // <--- AÑADIR LA REGIÓN AQUÍ
        value={`${consumption_analytics.financial_kpis.monthly_bill_estimate.total_bill_eur} €`}
        subtext={`Comparativa: Tu consumo es ${consumption_analytics.community_comparison.status} (Percentil ${consumption_analytics.community_comparison.percentile}%)`}
        icon={DollarSign}
        colorClass="text-purple-700"
        borderClass="border-purple-500"
      />
    </div>
  );
};

export default AnalysisResult;