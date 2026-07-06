import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const HourlyPatternsChart = ({ data }) => {
  if (!data || !data.average_consumption) return null;

  // Preparar datos: horas 0-23 y sus valores
  const chartData = data.hours.map((hour, index) => ({
    hour: `${hour}:00`,
    litros: data.average_consumption[index],
    isPeak: index === data.peak_hour
  }));

  return (
    <div className="card p-6 h-full">
      <h3 className="text-base font-bold text-slate-900 mb-1">Patrón horario</h3>
      <p className="text-xs text-slate-500 mb-4">Consumo medio por hora del día</p>

      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e1e0d9" />
            <XAxis dataKey="hour" fontSize={11} stroke="#898781" interval={2}
                   tickLine={false} axisLine={false} />
            <YAxis fontSize={11} stroke="#898781" tickFormatter={(v) => `${v} L`}
                   tickLine={false} axisLine={false} />
            <Tooltip
              cursor={{ fill: '#f1f5f9' }}
              contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }}
            />
            <Bar dataKey="litros" radius={[3, 3, 0, 0]}>
              {chartData.map((entry, index) => (
                /* Énfasis en la hora punta con un paso oscuro del MISMO azul (no otro tono) */
                <Cell key={`cell-${index}`} fill={entry.isPeak ? '#104281' : '#86b6ef'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-slate-400 mt-3">
        La barra oscura marca la hora punta promedio del hogar.
      </p>
    </div>
  );
};

export default HourlyPatternsChart;