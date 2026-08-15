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
}) => {
  const presets = [
    { id: '7d', label: '7 Days' },
    { id: '30d', label: '30 Days' },
    { id: '90d', label: '90 Days' },
    { id: '1y', label: '1 Year' },
    { id: 'all', label: 'ALL (Full History)' },
  ];

  return (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 shadow-lg backdrop-blur-sm">
      
      {/* Preset Range Buttons */}
      <div className="flex items-center flex-wrap gap-1.5">
        <span className="text-xs font-semibold text-zinc-400 flex items-center gap-1 mr-2">
          <Calendar className="w-3.5 h-3.5 text-zinc-300" /> Range:
        </span>
        {presets.map((preset) => (
          <button
            key={preset.id}
            onClick={() => onRangeChange(preset.id)}
            className={`tactile-button px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              range === preset.id
                ? 'bg-zinc-100 text-zinc-950 font-bold shadow-md'
                : 'bg-zinc-950/80 text-zinc-300 hover:bg-zinc-800 hover:text-white border border-zinc-800'
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Category Dropdown */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-zinc-400 flex items-center gap-1">
          <Filter className="w-3.5 h-3.5 text-zinc-300" /> Category:
        </span>
        <select
          value={selectedCategory}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="bg-zinc-950 text-zinc-200 text-xs font-medium rounded-lg px-3 py-1.5 border border-zinc-800 focus:outline-none focus:border-zinc-500 transition-colors"
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
