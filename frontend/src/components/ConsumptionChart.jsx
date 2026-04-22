import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ComposedChart, Scatter } from "recharts";

// Aceptamos una nueva prop: anomalousDays (Array de strings "YYYY-MM-DD")
const ConsumptionChart = ({ data, communityAvg, anomalousDays = [] }) => {
  if (!data || !data.labels) return null;

  const chartData = data.labels.map((date, index) => ({
    name: date,
    consumo: data.values[index],
    promedio: communityAvg,
    // Si la fecha está en la lista de malas, guardamos el valor para pintar el punto rojo
    anomaly: anomalousDays.includes(date) ? data.values[index] : null 
  }));

  return (
    <div className="bg-white rounded-2xl p-6 card-shadow border border-gray-100 h-full">
      <h3 className="text-lg font-bold text-gray-800 mb-6">Evolución del Consumo y Alertas</h3>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          {/* Usamos ComposedChart para mezclar Area (azul) y Scatter (puntos rojos) */}
          <ComposedChart data={chartData}>
            <defs>
              <linearGradient id="colorConsumo" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
            <XAxis dataKey="name" tickFormatter={(v) => v ? `${v.split('-')[2]}/${v.split('-')[1]}` : ''} fontSize={12} minTickGap={30} />
            <YAxis fontSize={12} tickFormatter={(v) => `${v}L`} />
            <Tooltip />
            <Legend verticalAlign="top" iconType="circle"/>
            
            {/* 1. Área de Consumo Normal */}
            <Area type="monotone" dataKey="consumo" name="Tu Consumo" stroke="#0ea5e9" fill="url(#colorConsumo)" strokeWidth={2} />
            
            {/* 2. Línea de Promedio */}
            <Area type="monotone" dataKey="promedio" name="Media Comunidad" stroke="#94a3b8" strokeDasharray="5 5" fill="transparent" />

            {/* 3. PUNTOS ROJOS (Anomalías) */}
            <Scatter name="Fuga Detectada" dataKey="anomaly" fill="red" shape="circle" />
            
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ConsumptionChart;