import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Sparkles, AlertCircle, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { LatestForecastProductGroup, ForecastPoint } from '../services/api';

interface GroupForecastTableProps {
  groups: LatestForecastProductGroup[];
  onSelectProduct?: (productId: number) => void;
}

export const GroupForecastTable: React.FC<GroupForecastTableProps> = ({ groups, onSelectProduct }) => {
  const navigate = useNavigate();

  if (!groups || groups.length === 0) {
    return (
      <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-8 text-center text-[#a1a1aa] empty-data-grid">
        <Sparkles className="w-6 h-6 mx-auto mb-2 text-zinc-600" />
        <p className="text-sm font-medium text-[#f4f4f5]">No product forecast records available</p>
        <p className="text-xs text-zinc-500 mt-1">Generate a forecast to populate product prediction details.</p>
      </div>
    );
  }

  // Calculate product metrics for table
  const tableData = groups.map((g) => {
    const total = g.forecast.reduce((acc, pt) => acc + Number(pt.predicted_units), 0);
    const avg = total / (g.forecast.length || 1);

    let peakPt = g.forecast[0];
    g.forecast.forEach((pt) => {
      if (Number(pt.predicted_units) > Number(peakPt.predicted_units)) {
        peakPt = pt;
      }
    });

    const peakDateStr = peakPt
      ? new Date(peakPt.forecast_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
      : 'N/A';

    return {
      product: g.product,
      forecastPoints: g.forecast,
      totalForecast: Math.round(total),
      avgDailyForecast: Number(avg.toFixed(1)),
      peakDayStr: `${peakDateStr} (${Math.round(Number(peakPt?.predicted_units || 0))} u)`
    };
  });

  // Global mean 7-day forecast total across catalog to determine relative levels
  const globalAvgTotal = tableData.reduce((acc, d) => acc + d.totalForecast, 0) / (tableData.length || 1);

  const getRelativeLevelBadge = (total: number) => {
    const ratio = globalAvgTotal > 0 ? total / globalAvgTotal : 1.0;
    if (ratio < 0.85) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">
          <ArrowDownRight className="w-3 h-3 text-zinc-400" />
          Low (&lt;0.85×)
        </span>
      );
    } else if (ratio > 1.15) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-purple-950/80 text-purple-300 border border-purple-800/60">
          <ArrowUpRight className="w-3 h-3 text-purple-400" />
          High (&gt;1.15×)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-zinc-800/60 text-zinc-300 border border-zinc-700/60">
        <Minus className="w-3 h-3 text-zinc-400" />
        Normal (0.85–1.15×)
      </span>
    );
  };

  const handleRowClick = (productId: number) => {
    if (onSelectProduct) {
      onSelectProduct(productId);
    } else {
      navigate(`/products/${productId}`);
    }
  };

  return (
    <div className="bg-[#18181b] border border-[#27272a] rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-[#27272a] flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-[#f4f4f5]">Product Forecast Intelligence Catalog</h3>
          <p className="text-xs text-[#a1a1aa] mt-0.5">
            7-day predicted volume and relative forecast intensity compared to store average.
          </p>
        </div>
        <span className="text-xs text-zinc-400 font-mono font-medium">{groups.length} Products</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-zinc-300">
          <thead className="bg-[#09090b] text-[#a1a1aa] font-semibold border-b border-[#27272a]">
            <tr>
              <th className="py-3 px-4">Product Name & SKU</th>
              <th className="py-3 px-4">Category</th>
              <th className="py-3 px-4 text-right">7-Day Forecast Total</th>
              <th className="py-3 px-4 text-right">Avg Daily Forecast</th>
              <th className="py-3 px-4">Peak Forecast Day</th>
              <th className="py-3 px-4">Relative Level</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#27272a]">
            {tableData.map((row) => (
              <tr
                key={row.product.id}
                onClick={() => handleRowClick(row.product.id)}
                className="hover:bg-zinc-800/50 cursor-pointer transition-colors group"
              >
                <td className="py-3 px-4">
                  <div className="font-semibold text-[#f4f4f5] group-hover:text-purple-300 transition-colors">
                    {row.product.name}
                  </div>
                  <div className="text-[11px] font-mono text-zinc-500">{row.product.sku}</div>
                </td>
                <td className="py-3 px-4">
                  <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700 text-[11px]">
                    {row.product.category || 'General'}
                  </span>
                </td>
                <td className="py-3 px-4 text-right font-mono font-semibold text-purple-300 text-sm">
                  {row.totalForecast.toLocaleString()} u
                </td>
                <td className="py-3 px-4 text-right font-mono text-zinc-300">
                  {row.avgDailyForecast} u/day
                </td>
                <td className="py-3 px-4 font-mono text-amber-300 font-medium">
                  {row.peakDayStr}
                </td>
                <td className="py-3 px-4">
                  {getRelativeLevelBadge(row.totalForecast)}
                </td>
                <td className="py-3 px-4 text-right">
                  <span className="inline-flex items-center text-xs text-zinc-400 group-hover:text-purple-300 font-medium gap-1">
                    Details
                    <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

interface SingleProductForecastTableProps {
  forecastPoints: ForecastPoint[];
  modelName?: string;
}

export const SingleProductForecastTable: React.FC<SingleProductForecastTableProps> = ({
  forecastPoints,
  modelName = 'XGBoost (xgb-v1)'
}) => {
  if (!forecastPoints || forecastPoints.length === 0) {
    return (
      <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6 text-center text-[#a1a1aa] empty-data-grid">
        <p className="text-xs text-zinc-500">No 7-day forecast points recorded for this product.</p>
      </div>
    );
  }

  // Calculate 7-day mean for relative level determination
  const total = forecastPoints.reduce((acc, p) => acc + Number(p.predicted_units), 0);
  const avg = total / (forecastPoints.length || 1);

  const getDayRelativeBadge = (units: number) => {
    const ratio = avg > 0 ? units / avg : 1.0;
    if (ratio < 0.85) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">
          Low (&lt;0.85× avg)
        </span>
      );
    } else if (ratio > 1.15) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-purple-950/80 text-purple-300 border border-purple-800/60">
          High (&gt;1.15× avg)
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-zinc-800/60 text-zinc-300 border border-zinc-700/60">
        Normal (0.85–1.15× avg)
      </span>
    );
  };

  return (
    <div className="bg-[#18181b] border border-[#27272a] rounded-xl overflow-hidden">
      <div className="p-4 border-b border-[#27272a] flex items-center justify-between">
        <h4 className="text-xs font-semibold text-[#f4f4f5] uppercase tracking-wider">7-Day Predicted Demand Breakdown</h4>
        <span className="text-xs font-mono text-purple-300">{modelName}</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-zinc-300">
          <thead className="bg-[#09090b] text-[#a1a1aa] font-semibold border-b border-[#27272a]">
            <tr>
              <th className="py-2.5 px-4">Date</th>
              <th className="py-2.5 px-4">Day of Week</th>
              <th className="py-2.5 px-4 text-right">Predicted Observed Units</th>
              <th className="py-2.5 px-4">Relative Level</th>
              <th className="py-2.5 px-4">Model Engine</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#27272a]">
            {forecastPoints.map((pt) => {
              const d = new Date(pt.forecast_date);
              const dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
              const dayStr = d.toLocaleDateString('en-US', { weekday: 'long' });
              const units = Number(pt.predicted_units);

              return (
                <tr key={pt.forecast_date} className="hover:bg-zinc-800/30">
                  <td className="py-2.5 px-4 font-mono font-medium text-[#f4f4f5]">{dateStr}</td>
                  <td className="py-2.5 px-4 text-zinc-400">{dayStr}</td>
                  <td className="py-2.5 px-4 text-right font-mono font-semibold text-purple-300 text-sm">
                    {units.toFixed(1)}
                  </td>
                  <td className="py-2.5 px-4">{getDayRelativeBadge(units)}</td>
                  <td className="py-2.5 px-4 text-zinc-400 font-mono text-[11px]">{modelName}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
