import { useState } from 'react';
import { Droplets, LogIn } from 'lucide-react';
import { login } from '../services/api';

/** Pantalla de acceso (solo aparece cuando el backend tiene tenants configurados). */
export default function LoginScreen({ onLoggedIn }) {
  const [tenantId, setTenantId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await login(tenantId.trim(), password);
      onLoggedIn(res.tenant);
    } catch (err) {
      setError(err?.response?.status === 401
        ? 'Usuario o contraseña incorrectos.'
        : 'No se pudo conectar con el servidor.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid place-items-center p-6" style={{ background: 'var(--sidebar)' }}>
      <form onSubmit={submit} className="card p-8 w-full max-w-sm space-y-5">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-sky-500 to-blue-700 text-white p-2.5 rounded-xl">
            <Droplets size={22} strokeWidth={2.5} />
          </div>
          <div>
            <h1 className="font-bold text-lg text-slate-900">Smart Water Monitor</h1>
            <p className="text-xs text-slate-500">Consola de operaciones</p>
          </div>
        </div>

        <label className="block">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Cliente</span>
          <input
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            autoComplete="username"
            required
            className="mt-1.5 w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="id-de-cliente"
          />
        </label>

        <label className="block">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Contraseña</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
            className="mt-1.5 w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="••••••••"
          />
        </label>

        {error && <p className="text-sm text-red-600 font-medium">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2.5 font-semibold text-sm transition-colors disabled:opacity-50"
        >
          <LogIn size={16} />
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  );
}
