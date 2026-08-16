import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Legend
} from 'recharts';
import { Sparkles, Calendar, Layers } from 'lucide-react';

export interface ForecastChartPoint {
  date: string;
  historical_units?: number | null;
  forecast_units?: number | null;
  is_boundary?: boolean;
}

interface ForecastChartProps {
  historicalData: Array<{ sale_date: string; units_sold: number }>;
  forecastData: Array<{ forecast_date: string; predicted_units: number }>;
  modelName?: string;
  modelVersion?: string;
  height?: number;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  historicalData,
  forecastData,
  modelName = 'XGBoost',
  modelVersion = 'xgb-v1',
  height = 340
}) => {
  const { chartData, boundaryDate } = useMemo(() => {
    if (!forecastData || forecastData.length === 0) {
      return { chartData: [], boundaryDate: null };
    }

    // Sort historical data by date
    const sortedHist = [...historicalData].sort((a, b) => a.sale_date.localeCompare(b.sale_date));
    // Filter to last 28 days of history for clear visual comparison
    const recentHist = sortedHist.slice(-28);

    // Sort forecast data by date
    const sortedFcst = [...forecastData].sort((a, b) => a.forecast_date.localeCompare(b.forecast_date));
    const firstForecastDate = sortedFcst[0]?.forecast_date || null;

    const data: ForecastChartPoint[] = [];

    // Append historical points
    recentHist.forEach((h, idx) => {
      const isLastHist = idx === recentHist.length - 1;
      data.push({
        date: h.sale_date,
        historical_units: h.units_sold,
        // Connect last historical point to first forecast point seamlessly
        forecast_units: isLastHist ? h.units_sold : null,
        is_boundary: isLastHist
      });
    });

    // Append forecast points
    sortedFcst.forEach((f) => {
      data.push({
        date: f.forecast_date,
        historical_units: null,
        forecast_units: Number(f.predicted_units),
        is_boundary: false
      });
    });

    return { chartData: data, boundaryDate: firstForecastDate };
  }, [historicalData, forecastData]);

  // Format date helper
  const formatDateLabel = (str: string) => {
    try {
      const d = new Date(str);
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return str;
    }
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || payload.length === 0) return null;

    const pointData: ForecastChartPoint = payload[0].payload;
    const isForecast = pointData.forecast_units !== null && pointData.historical_units === null;

    return (
      <div className="bg-[#18181b] border border-[#3f3f46] p-3 rounded-lg shadow-xl text-xs space-y-2">
        <div className="flex items-center justify-between gap-3 border-b border-[#27272a] pb-1.5">
          <span className="font-semibold text-[#f4f4f5] flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[#a1a1aa]" />
            {new Date(pointData.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
          </span>
          {isForecast ? (
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-950/80 text-purple-300 border border-purple-800/60 flex items-center gap-1">
              <Sparkles className="w-2.5 h-2.5" />
              AI Forecast
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-zinc-800 text-zinc-300 border border-zinc-700">
              Observed History
            </span>
          )}
        </div>

        {pointData.historical_units !== null && pointData.historical_units !== undefined && (
          <div className="flex items-center justify-between gap-4 text-zinc-300">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-zinc-400 inline-block"></span>
              Observed Units Sold:
            </span>
            <span className="font-semibold text-[#f4f4f5]">{pointData.historical_units} units</span>
          </div>
        )}

        {pointData.forecast_units !== null && pointData.forecast_units !== undefined && !pointData.is_boundary && (
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-4 text-purple-300">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-purple-400 inline-block"></span>
                Predicted Observed Units:
              </span>
              <span className="font-semibold text-purple-200 text-sm">{pointData.forecast_units} units</span>
            </div>
            <div className="pt-1 text-[10px] text-zinc-400 border-t border-zinc-800/80 flex items-center justify-between">
              <span>Model: <strong className="text-zinc-300">{modelName}</strong></span>
              <span>Version: <strong className="text-zinc-300">{modelVersion}</strong></span>
            </div>
          </div>
        )}
      </div>
    );
  };

  if (!chartData || chartData.length === 0) {
    return (
      <div
        style={{ height }}
        className="w-full bg-[#18181b] border border-[#27272a] rounded-xl flex flex-col items-center justify-center p-6 text-center empty-data-grid"
      >
        <Sparkles className="w-8 h-8 text-zinc-600 mb-2" />
        <h4 className="text-sm font-semibold text-[#f4f4f5]">7-Day Forecast Not Generated</h4>
        <p className="text-xs text-[#a1a1aa] mt-1 max-w-sm">
          Generate a forecast using the latest available historical sales data.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full bg-[#18181b] border border-[#27272a] rounded-xl p-5 shadow-sm animate-forecast-projection">
      {/* Header & Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-[#27272a]">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
            <h3 className="text-sm font-semibold text-[#f4f4f5]">Observed Sales History vs 7-Day AI Forecast</h3>
          </div>
          <p className="text-xs text-[#a1a1aa] mt-0.5">
            Continuous boundary transition from historical observed units sold to predicted 7-day demand.
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 text-zinc-400">
            <span className="w-3.5 h-0.5 bg-zinc-400 inline-block"></span>
            <span>Historical Observed</span>
          </div>
          <div className="flex items-center gap-1.5 text-purple-400 font-medium">
            <span className="w-3.5 h-0.5 bg-purple-400 border-b border-dashed border-purple-300 inline-block"></span>
            <span>7-Day AI Forecast</span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 20, right: 20, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDateLabel}
              stroke="#71717a"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#27272a' }}
            />
            <YAxis
              stroke="#71717a"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#27272a' }}
              tickFormatter={(v) => `${v}`}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Forecast Boundary Marker */}
            {boundaryDate && (
              <ReferenceLine
                x={boundaryDate}
                stroke="#a855f7"
                strokeDasharray="4 4"
                strokeWidth={1.5}
                label={{
                  value: 'Forecast begins',
                  position: 'top',
                  fill: '#c084fc',
                  fontSize: 11,
                  fontWeight: 600,
                  offset: 8
                }}
              />
            )}

            {/* Historical Observed Line */}
            <Line
              type="monotone"
              dataKey="historical_units"
              stroke="#a1a1aa"
              strokeWidth={2}
              dot={{ r: 2, fill: '#a1a1aa', stroke: '#18181b', strokeWidth: 1 }}
              activeDot={{ r: 4, fill: '#f4f4f5' }}
              connectNulls={false}
            />

            {/* Forecast Predicted Line */}
            <Line
              type="monotone"
              dataKey="forecast_units"
              stroke="#c084fc"
              strokeWidth={2.5}
              strokeDasharray="6 4"
              dot={{ r: 3, fill: '#c084fc', stroke: '#18181b', strokeWidth: 1 }}
              activeDot={{ r: 5, fill: '#e9d5ff' }}
              connectNulls={true}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
