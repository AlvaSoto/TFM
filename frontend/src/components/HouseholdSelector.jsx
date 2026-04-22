import React from 'react';
import { Home } from 'lucide-react';

// CORRECCIÓN 1: Valor por defecto "households = []" para evitar undefined
const HouseholdSelector = ({ households = [], selectedHouse, setSelectedHouse, disabled }) => {
  return (
    <div className="flex flex-col flex-grow min-w-[250px]">
      <label htmlFor="household-select" className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide flex items-center gap-1">
        <Home size={14} /> Seleccionar Hogar
      </label>
      <div className="relative">
        <select 
          id="household-select"
          className="w-full border border-gray-300 p-2.5 pl-3 pr-8 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none transition-shadow disabled:opacity-50 disabled:cursor-not-allowed text-gray-700"
          value={selectedHouse}
          onChange={(e) => setSelectedHouse(e.target.value)}
          disabled={disabled}
        >
          <option value="">-- Elige una casa --</option>
          
          {/* CORRECCIÓN 2: "households?." verifica que existe antes de hacer map */}
          {households?.map((house) => (
            <option key={house.id} value={house.id}>
              {house.label}
            </option>
          ))}
          
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
          <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
        </div>
      </div>
    </div>
  );
};

export default HouseholdSelector;