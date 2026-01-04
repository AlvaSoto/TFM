import React from 'react';
import { motion } from "framer-motion";
import { DollarSign, TrendingUp, TrendingDown, Calendar } from "lucide-react";

const CostEstimateCard = ({ kpis, region }) => {
  const bill = kpis.monthly_bill_estimate.total_bill_eur;
  const trend = kpis.trend_vs_last_week;
  const isGood = trend < 0;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.1 }}
      className="bg-white rounded-2xl p-6 card-shadow border border-gray-100"
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Factura Estimada (Mes)</p>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-3xl font-bold text-gray-800">{bill}</span>
            <span className="text-lg text-gray-500">€</span>
          </div>
        </div>
        <div className="p-2 bg-purple-50 rounded-lg">
          <DollarSign className="w-6 h-6 text-purple-600" />
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500 flex items-center gap-1">
            <Calendar size={14}/> Región
          </span>
          <span className="font-medium text-gray-700">{region}</span>
        </div>
        
        <div className={`flex items-center gap-2 text-sm p-2 rounded-lg ${isGood ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {isGood ? <TrendingDown size={16} /> : <TrendingUp size={16} />}
          <span className="font-medium">
            {Math.abs(trend)}% {isGood ? 'menos' : 'más'} que la semana pasada
          </span>
        </div>
      </div>
    </motion.div>
  );
};

export default CostEstimateCard;