import React from 'react';
import { TrendingUp, TrendingDown, Calendar } from 'lucide-react';

const DailyTrendCard = ({ dailyData }) => {
  const isSaving = dailyData.trend_percent < 0; // Si es negativo, estamos ahorrando

  return (
    <div className="bg-white rounded-2xl p-6 card-shadow border border-gray-100">
      <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Consumo Último Día ({dailyData.date})</p>
      
      <div className="flex items-baseline gap-2 mb-4">
        <span className="text-4xl font-extrabold text-blue-600">{dailyData.today_l}</span>
        <span className="text-lg font-medium text-gray-500">Litros</span>
      </div>

      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-bold ${
        isSaving ? 'bg-emerald-100 text-emerald-700' : 'bg-orange-100 text-orange-700'
      }`}>
        {isSaving ? <TrendingDown size={16} /> : <TrendingUp size={16} />}
        <span>
          {Math.abs(dailyData.trend_percent)}% {isSaving ? 'menos' : 'más'} que ayer
        </span>
      </div>
      
      <p className="text-xs text-gray-400 mt-3">
        Ayer consumiste {dailyData.yesterday_l} L
      </p>
    </div>
  );
};

export default DailyTrendCard;