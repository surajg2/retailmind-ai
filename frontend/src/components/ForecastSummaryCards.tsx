import React, { useMemo } from 'react';
import { Calendar, TrendingUp, Sparkles, BarChart3, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { ForecastPoint } from '../services/api';

interface ForecastSummaryCardsProps {
  forecastPoints: ForecastPoint[];
  historicalDailyAvg?: number;
}

export const ForecastSummaryCards: React.FC<ForecastSummaryCardsProps> = ({
  forecastPoints,
  historicalDailyAvg = 0
}) => {
  const summary = useMemo(() => {
    if (!forecastPoints || forecastPoints.length === 0) {
      return {
        totalForecast: 0,
        avgDailyForecast: 0,
        peakDay: { date: 'N/A', units: 0 },
        pctvsHistorical: null
      };
    }

    const total = forecastPoints.reduce((acc, curr) => acc + Number(curr.predicted_units), 0);
    const avg = total / forecastPoints.length;

    let peak = forecastPoints[0];
    forecastPoints.forEach((p) => {
      if (Number(p.predicted_units) > Number(peak.predicted_units)) {
        peak = p;
      }
    });

    let pctChange: number | null = null;
    if (historicalDailyAvg > 0) {
      pctChange = ((avg - historicalDailyAvg) / historicalDailyAvg) * 100;
    }

    return {
      totalForecast: Math.round(total),
      avgDailyForecast: Number(avg.toFixed(1)),
      peakDay: {
        date: peak ? new Date(peak.forecast_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }) : 'N/A',
        units: peak ? Math.round(Number(peak.predicted_units)) : 0
      },
      pctvsHistorical: pctChange !== null ? Number(pctChange.toFixed(1)) : null
    };
  }, [forecastPoints, historicalDailyAvg]);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. 7-Day Forecast Total */}
      <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4 tactile-card flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-[#a1a1aa] uppercase tracking-wider">7-Day Forecast Total</span>
          <div className="p-2 rounded-lg bg-purple-950/60 border border-purple-800/50 text-purple-400">
            <Sparkles className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-[#f4f4f5] font-mono">{summary.totalForecast.toLocaleString()} <span className="text-xs font-normal text-[#a1a1aa]">units</span></div>
          <p className="text-[11px] text-zinc-500 mt-1">Sum of 7 predicted daily units</p>
        </div>
      </div>

      {/* 2. Average Daily Forecast */}
      <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4 tactile-card flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-[#a1a1aa] uppercase tracking-wider">Average Daily Forecast</span>
          <div className="p-2 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-300">
            <BarChart3 className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-[#f4f4f5] font-mono">{summary.avgDailyForecast} <span className="text-xs font-normal text-[#a1a1aa]">units / day</span></div>
          <p className="text-[11px] text-zinc-500 mt-1">Mean 7-day predicted volume</p>
        </div>
      </div>

      {/* 3. Peak Forecast Day */}
      <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4 tactile-card flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-[#a1a1aa] uppercase tracking-wider">Peak Forecast Day</span>
          <div className="p-2 rounded-lg bg-amber-950/60 border border-amber-800/50 text-amber-400">
            <Calendar className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-[#f4f4f5] font-mono">{summary.peakDay.units} <span className="text-xs font-normal text-[#a1a1aa]">units</span></div>
          <p className="text-xs font-medium text-amber-400 mt-1 flex items-center gap-1">
            <span>Highest on {summary.peakDay.date}</span>
          </p>
        </div>
      </div>

      {/* 4. Forecast vs Recent Average */}
      <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4 tactile-card flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-[#a1a1aa] uppercase tracking-wider">Forecast vs History</span>
          <div className="p-2 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-300">
            <TrendingUp className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3">
          {summary.pctvsHistorical !== null ? (
            <div>
              <div className="flex items-center gap-1.5 text-2xl font-bold font-mono">
                {summary.pctvsHistorical >= 0 ? (
                  <span className="text-emerald-400 flex items-center gap-0.5">
                    +{summary.pctvsHistorical}%
                    <ArrowUpRight className="w-5 h-5 inline" />
                  </span>
                ) : (
                  <span className="text-rose-400 flex items-center gap-0.5">
                    {summary.pctvsHistorical}%
                    <ArrowDownRight className="w-5 h-5 inline" />
                  </span>
                )}
              </div>
              <p className="text-[11px] text-[#a1a1aa] mt-1">
                vs recent observed average ({Math.round(historicalDailyAvg)} u/day)
              </p>
            </div>
          ) : (
            <div>
              <div className="text-xl font-bold text-zinc-400">--</div>
              <p className="text-[11px] text-zinc-500 mt-1">vs recent observed average</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
