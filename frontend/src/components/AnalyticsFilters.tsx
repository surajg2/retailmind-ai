import React from 'react';
import { Calendar, Filter } from 'lucide-react';

interface AnalyticsFiltersProps {
  range: string;
  onRangeChange: (range: string) => void;
  selectedCategory: string;
  onCategoryChange: (category: string) => void;
  categories: string[];
  startDate?: string;
  endDate?: string;
  onCustomDateChange?: (start?: string, end?: string) => void;
}

export const AnalyticsFilters: React.FC<AnalyticsFiltersProps> = ({
  range,
  onRangeChange,
  selectedCategory,
  onCategoryChange,
  categories,
  startDate,
  endDate,
  onCustomDateChange
}) => {
  const presets = [
    { id: '7d', label: '7 Days' },
    { id: '30d', label: '30 Days' },
    { id: '90d', label: '90 Days' },
    { id: '1y', label: '1 Year' },
    { id: 'all', label: 'ALL (Full History)' },
  ];

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 shadow-lg backdrop-blur-sm">
      
      {/* Preset Range Buttons */}
      <div className="flex items-center flex-wrap gap-1.5">
        <span className="text-xs font-semibold text-slate-400 flex items-center gap-1 mr-2">
          <Calendar className="w-3.5 h-3.5 text-cyan-400" /> Range:
        </span>
        {presets.map((preset) => (
          <button
            key={preset.id}
            onClick={() => onRangeChange(preset.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              range === preset.id
                ? 'bg-cyan-500 text-slate-950 font-semibold shadow-md shadow-cyan-500/20'
                : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700/80 hover:text-white'
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Category Dropdown */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-slate-400 flex items-center gap-1">
          <Filter className="w-3.5 h-3.5 text-cyan-400" /> Category:
        </span>
        <select
          value={selectedCategory}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="bg-slate-800 text-slate-200 text-xs font-medium rounded-lg px-3 py-1.5 border border-slate-700 focus:outline-none focus:border-cyan-500 transition-colors"
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>

    </div>
  );
};
