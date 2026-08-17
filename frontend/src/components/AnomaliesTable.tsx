import React, { useState } from 'react';
import { AlertOctagon, Filter, ShieldAlert, Sparkles, TrendingUp, TrendingDown, DollarSign, Calendar } from 'lucide-react';
import { AnomalyItem } from '../services/api';

interface AnomaliesTableProps {
  anomalies: AnomalyItem[];
  categories?: string[];
  onSelectProduct?: (productId: number) => void;
  onFilterChange?: (filters: { severity?: string; anomaly_type?: string; category?: string }) => void;
}

export const AnomaliesTable: React.FC<AnomaliesTableProps> = ({
  anomalies,
  categories = [],
  onSelectProduct,
  onFilterChange
}) => {
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedCat, setSelectedCat] = useState<string>('ALL');

  const handleSeverityChange = (val: string) => {
    setSelectedSeverity(val);
    if (onFilterChange) {
      onFilterChange({
        severity: val === 'ALL' ? undefined : val,
        anomaly_type: selectedType === 'ALL' ? undefined : selectedType,
        category: selectedCat === 'ALL' ? undefined : selectedCat
      });
    }
  };

  const handleTypeChange = (val: string) => {
    setSelectedType(val);
    if (onFilterChange) {
      onFilterChange({
        severity: selectedSeverity === 'ALL' ? undefined : selectedSeverity,
        anomaly_type: val === 'ALL' ? undefined : val,
        category: selectedCat === 'ALL' ? undefined : selectedCat
      });
    }
  };

  const handleCatChange = (val: string) => {
    setSelectedCat(val);
    if (onFilterChange) {
      onFilterChange({
        severity: selectedSeverity === 'ALL' ? undefined : selectedSeverity,
        anomaly_type: selectedType === 'ALL' ? undefined : selectedType,
        category: val === 'ALL' ? undefined : val
      });
    }
  };

  const filtered = anomalies.filter((a) => {
    if (selectedSeverity !== 'ALL' && a.severity !== selectedSeverity) return false;
    if (selectedType !== 'ALL' && a.anomaly_type !== selectedType) return false;
    if (selectedCat !== 'ALL' && a.category !== selectedCat) return false;
    return true;
  });

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'HIGH_SALES':
        return (
          <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 font-mono">
            <TrendingUp className="w-3 h-3 text-emerald-400" /> HIGH SALES
          </span>
        );
      case 'LOW_SALES':
        return (
          <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1 font-mono">
            <TrendingDown className="w-3 h-3 text-amber-400" /> LOW SALES
          </span>
        );
      case 'ZERO_SALES':
        return (
          <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1 font-mono">
            <AlertOctagon className="w-3 h-3 text-rose-400" /> ZERO SALES
          </span>
        );
      case 'PROMOTION_SPIKE':
        return (
          <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-300 border border-purple-500/30 flex items-center gap-1 font-mono">
            <Sparkles className="w-3 h-3 text-purple-400" /> PROMO SPIKE
          </span>
        );
      case 'PRICE_CHANGE':
        return (
          <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-zinc-800 text-zinc-200 border border-zinc-700 flex items-center gap-1 font-mono">
            <DollarSign className="w-3 h-3 text-zinc-300" /> PRICE CHANGE
          </span>
        );
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] bg-zinc-800 text-zinc-400 font-mono">{type}</span>;
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 font-mono animate-pulse">
            CRITICAL
          </span>
        );
      case 'WARNING':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 font-mono">
            WARNING
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-zinc-800 text-zinc-400 border border-zinc-700 font-mono">
            INFO
          </span>
        );
    }
  };

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-2xl p-5 shadow-xl backdrop-blur-md space-y-4">
      
      {/* Header & Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div className="flex items-center gap-2">
          <AlertOctagon className="w-5 h-5 text-amber-400" />
          <div>
            <h3 className="text-sm font-bold text-zinc-200 tracking-wide">Historical Sales & Demand Anomalies</h3>
            <p className="text-[11px] text-zinc-400">
              Statistical deviation detection via 21-day rolling median & Median Absolute Deviation (MAD)
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <div className="flex items-center gap-1.5 bg-zinc-950/80 border border-zinc-800 px-3 py-1.5 rounded-lg">
            <Filter className="w-3.5 h-3.5 text-zinc-400" />
            <span className="text-zinc-500 font-sans">Severity:</span>
            <select
              value={selectedSeverity}
              onChange={(e) => handleSeverityChange(e.target.value)}
              className="bg-transparent text-zinc-200 focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-zinc-900">ALL</option>
              <option value="CRITICAL" className="bg-zinc-900">CRITICAL</option>
              <option value="WARNING" className="bg-zinc-900">WARNING</option>
              <option value="INFO" className="bg-zinc-900">INFO</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 bg-zinc-950/80 border border-zinc-800 px-3 py-1.5 rounded-lg">
            <span className="text-zinc-500 font-sans">Type:</span>
            <select
              value={selectedType}
              onChange={(e) => handleTypeChange(e.target.value)}
              className="bg-transparent text-zinc-200 focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-zinc-900">ALL TYPES</option>
              <option value="HIGH_SALES" className="bg-zinc-900">HIGH SALES</option>
              <option value="LOW_SALES" className="bg-zinc-900">LOW SALES</option>
              <option value="ZERO_SALES" className="bg-zinc-900">ZERO SALES</option>
              <option value="PROMOTION_SPIKE" className="bg-zinc-900">PROMO SPIKE</option>
              <option value="PRICE_CHANGE" className="bg-zinc-900">PRICE CHANGE</option>
            </select>
          </div>

          {categories.length > 0 && (
            <div className="flex items-center gap-1.5 bg-zinc-950/80 border border-zinc-800 px-3 py-1.5 rounded-lg">
              <span className="text-zinc-500 font-sans">Category:</span>
              <select
                value={selectedCat}
                onChange={(e) => handleCatChange(e.target.value)}
                className="bg-transparent text-zinc-200 focus:outline-none cursor-pointer"
              >
                <option value="ALL" className="bg-zinc-900">ALL CATEGORIES</option>
                {categories.map((c) => (
                  <option key={c} value={c} className="bg-zinc-900">{c}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Anomalies Data Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="text-zinc-400 border-b border-zinc-800 bg-zinc-950/80 font-mono">
              <th className="py-3 px-4 font-semibold">Date</th>
              <th className="py-3 px-4 font-semibold">SKU & Product</th>
              <th className="py-3 px-4 font-semibold">Category</th>
              <th className="py-3 px-4 font-semibold">Anomaly Type</th>
              <th className="py-3 px-4 font-semibold">Severity</th>
              <th className="py-3 px-4 font-semibold">Observed vs Baseline</th>
              <th className="py-3 px-4 font-semibold">Context Flags</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60 font-mono">
            {filtered.map((item, idx) => (
              <tr
                key={`${item.product_id}-${item.date}-${item.anomaly_type}-${idx}`}
                onClick={() => onSelectProduct && onSelectProduct(item.product_id)}
                className="hover:bg-zinc-800/40 transition-colors cursor-pointer"
              >
                <td className="py-3 px-4 font-semibold text-zinc-300 whitespace-nowrap">{item.date}</td>
                <td className="py-3 px-4">
                  <div className="font-bold text-zinc-200">{item.sku}</div>
                  <div className="text-[11px] text-zinc-400 font-sans line-clamp-1">{item.product_name}</div>
                </td>
                <td className="py-3 px-4 text-zinc-400 font-sans">{item.category || 'General'}</td>
                <td className="py-3 px-4">{getTypeBadge(item.anomaly_type)}</td>
                <td className="py-3 px-4">{getSeverityBadge(item.severity)}</td>
                <td className="py-3 px-4">
                  <div className="font-bold text-zinc-100">
                    {item.observed_units} pcs <span className="text-zinc-500 font-normal">vs {item.baseline_units} baseline</span>
                  </div>
                  <div className="text-[10px] text-zinc-400">
                    Deviation: <strong className={item.deviation >= 0 ? 'text-emerald-400' : 'text-rose-400'}>{item.deviation > 0 ? `+${item.deviation}` : item.deviation}</strong> (Z: {item.deviation_score})
                  </div>
                </td>
                <td className="py-3 px-4">
                  <div className="flex flex-wrap gap-1 font-sans text-[10px]">
                    {item.is_stockout && (
                      <span className="px-1.5 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-800/50 flex items-center gap-1">
                        <ShieldAlert className="w-2.5 h-2.5 text-rose-400" /> Stockout
                      </span>
                    )}
                    {item.promotion && (
                      <span className="px-1.5 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800/50">
                        Promo Active
                      </span>
                    )}
                    {item.holiday && (
                      <span className="px-1.5 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800/50">
                        Holiday
                      </span>
                    )}
                    {item.festival && (
                      <span className="px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/50">
                        {item.festival}
                      </span>
                    )}
                    {item.price_change_percentage !== null && item.price_change_percentage !== undefined && (
                      <span className="px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                        Price {item.price_change_percentage > 0 ? `+${item.price_change_percentage}%` : `${item.price_change_percentage}%`}
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            ))}

            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-zinc-500 font-sans">
                  No anomalies detected for selected filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
