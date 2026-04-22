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
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
        🕒 Patrón de Consumo Horario (Media)
      </h3>
      
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb"/>
            <XAxis dataKey="hour" fontSize={11} stroke="#9ca3af" interval={2} />
            <YAxis fontSize={12} stroke="#9ca3af" tickFormatter={(v) => `${v} L`}/>
            <Tooltip 
              cursor={{fill: '#f3f4f6'}}
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            />
            <Bar dataKey="litros" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.isPeak ? '#8b5cf6' : '#93c5fd'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="text-sm text-gray-500 mt-4">
        * La barra morada indica la hora punta promedio.
      </p>
    </div>
  );
};

export default HourlyPatternsChart;