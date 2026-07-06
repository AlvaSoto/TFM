import { useState, useEffect } from 'react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { getFleetTrends } from '../services/api';

/**
 * Tendencias de la red: dos paneles apilados con el mismo eje temporal.
 * (Unidades distintas => nunca doble eje; dos gráficas pequeñas.)
 *  1. Consumo agregado diario de la red (m³) — serie azul.
 *  2. Hogares con anomalía por día — barras en color de estado.
 */

const VIZ = {
  series: '#2a78d6',
  seriesSoft: '#cde2fb',
  critical: '#d03b3b',
  grid: '#e1e0d9',
  muted: '#898781',
};

const fmtDay = (d) => (d ? `${d.split('-')[2]}/${d.split('-')[1]}` : '');

export default function NetworkTrendChart() {
  const [trends, setTrends] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getFleetTrends().then(setTrends).catch(() => setError(true));
  }, []);

  if (error) return null;

  if (!trends) {
    return (
      <div className="card p-6">
        <div className="skeleton h-4 w-48 mb-4"></div>
        <div className="skeleton h-40 w-full"></div>
      </div>
    );
  }

  const rows = trends.labels.map((d, i) => ({
    day: d,
    m3: trends.network_m3[i],
    alerts: trends.households_in_alert[i],
  }));

  return (
    <div className="card p-6">
      <div className="mb-1">
        <h2 className="text-base font-bold text-slate-900">Consumo agregado de la red</h2>
        <p className="text-xs text-slate-500">m³/día sobre toda la flota monitorizada</p>
      </div>

      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={rows} margin={{ top: 12, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="netFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={VIZ.series} stopOpacity={0.25} />
                <stop offset="100%" stopColor={VIZ.series} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke={VIZ.grid} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="day" tickFormatter={fmtDay} fontSize={11} stroke={VIZ.muted}
                   minTickGap={40} tickLine={false} axisLine={false} />
            <YAxis fontSize={11} stroke={VIZ.muted} tickFormatter={(v) => `${v}`}
                   width={44} tickLine={false} axisLine={false}
                   label={{ value: 'm³', position: 'insideTopLeft', fontSize: 10, fill: VIZ.muted, dy: -10 }} />
            <Tooltip
              formatter={(v) => [`${v} m³`, 'Consumo red']}
              labelFormatter={(d) => d}
              contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }}
            />
            <Area type="monotone" dataKey="m3" stroke={VIZ.series} strokeWidth={2}
                  fill="url(#netFill)" dot={false} activeDot={{ r: 4 }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 mb-1">
        <h3 className="text-sm font-semibold text-slate-700">Hogares con anomalía por día</h3>
      </div>
      <div className="h-24">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
            <XAxis dataKey="day" tickFormatter={fmtDay} fontSize={11} stroke={VIZ.muted}
                   minTickGap={40} tickLine={false} axisLine={false} />
            <YAxis fontSize={11} stroke={VIZ.muted} width={44} allowDecimals={false}
                   tickLine={false} axisLine={false} />
            <Tooltip
              formatter={(v) => [`${v} hogares`, 'En anomalía']}
              labelFormatter={(d) => d}
              contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }}
            />
            <Bar dataKey="alerts" radius={[3, 3, 0, 0]} maxBarSize={6}>
              {rows.map((r, i) => (
                <Cell key={i} fill={r.alerts > 0 ? VIZ.critical : VIZ.grid} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
