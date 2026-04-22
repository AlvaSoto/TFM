import React from 'react';
import { MapPin } from 'lucide-react';

const RegionSelector = ({ regions, selectedRegion, setSelectedRegion, disabled }) => {
  return (
    <div className="flex flex-col flex-grow min-w-[200px]">
      <label htmlFor="region-select" className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide flex items-center gap-1">
        <MapPin size={14} /> Región (Tarifa)
      </label>
      <div className="relative">
        <select 
          id="region-select"
          className="w-full border border-gray-300 p-2.5 pl-3 pr-8 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none transition-shadow disabled:opacity-50 disabled:cursor-not-allowed text-gray-700"
          value={selectedRegion}
          onChange={(e) => setSelectedRegion(e.target.value)}
          disabled={disabled}
        >
          {regions.map((reg) => (
            <option key={reg} value={reg}>{reg}</option>
          ))}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
          <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
        </div>
      </div>
    </div>
  );
};

export default RegionSelector;