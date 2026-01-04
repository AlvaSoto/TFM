import React from 'react';
import { FileText } from 'lucide-react';

const BillHistory = ({ history, currentRegion }) => {
  return (
    <div className="bg-white rounded-2xl p-6 card-shadow border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <FileText className="text-gray-400" size={20}/>
          Historial de Facturas
        </h3>
        <span className="text-xs font-medium bg-gray-100 px-2 py-1 rounded text-gray-500">
          Tarifa: {currentRegion}
        </span>
      </div>

      <div className="overflow-hidden">
        <table className="w-full text-left text-sm text-gray-600">
          <thead className="bg-gray-50 text-xs uppercase font-semibold text-gray-500">
            <tr>
              <th className="px-4 py-3">Mes</th>
              <th className="px-4 py-3">Consumo</th>
              <th className="px-4 py-3 text-right">Importe</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {history.slice(0, 5).map((bill, i) => ( // Mostramos solo los últimos 5
              <tr key={i} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-800">{bill.month_name}</td>
                <td className="px-4 py-3">{bill.consumption_l} L</td>
                <td className="px-4 py-3 text-right font-bold text-slate-700">
                  {bill.total_bill} €
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default BillHistory;