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
    <div className="card p-6 h-full">
      <h3 className="text-base font-bold text-slate-900 mb-1">Evolución del consumo y alertas</h3>
      <p className="text-xs text-slate-500 mb-4">Litros/día frente a la media de hogares similares</p>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          {/* ComposedChart: área (serie azul) + scatter (días anómalos, color de estado) */}
          <ComposedChart data={chartData}>
            <defs>
              <linearGradient id="colorConsumo" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2a78d6" stopOpacity={0.22} />
                <stop offset="95%" stopColor="#2a78d6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" vertical={false} />
            <XAxis dataKey="name" tickFormatter={(v) => v ? `${v.split('-')[2]}/${v.split('-')[1]}` : ''}
                   fontSize={11} minTickGap={30} stroke="#898781" tickLine={false} axisLine={false} />
            <YAxis fontSize={11} tickFormatter={(v) => `${v}L`} stroke="#898781"
                   tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }} />
            <Legend verticalAlign="top" iconType="circle" wrapperStyle={{ fontSize: 12 }} />

            <Area type="monotone" dataKey="consumo" name="Tu consumo" stroke="#2a78d6"
                  fill="url(#colorConsumo)" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
            <Area type="monotone" dataKey="promedio" name="Media comunidad" stroke="#898781"
                  strokeDasharray="5 5" fill="transparent" dot={false} />
            <Scatter name="Día anómalo" dataKey="anomaly" fill="#d03b3b" shape="circle" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ConsumptionChart;