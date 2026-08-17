import React from 'react';
import { Target, Activity, Percent, Layers, ShieldAlert, CheckCircle2, AlertTriangle } from 'lucide-react';
import { ForecastEvaluationSummary } from '../services/api';

interface ForecastEvaluationCardsProps {
  summary: ForecastEvaluationSummary | null;
}

export const ForecastEvaluationCards: React.FC<ForecastEvaluationCardsProps> = ({ summary }) => {
  if (!summary || summary.status === 'INSUFFICIENT_EVALUATION_DATA') {
    return (
      <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-5 text-center text-zinc-400 backdrop-blur-sm empty-data-grid">
        <Target className="w-6 h-6 mx-auto mb-2 text-zinc-500" />
        <span className="text-xs font-semibold text-zinc-300 block">Insufficient Evaluation Data</span>
        <p className="text-[11px] text-zinc-500 max-w-md mx-auto mt-1">
          No persisted predictions match historical observed sales target dates yet. Evaluation metrics require forecast dates that have passed into historical record.
        </p>
      </div>
    );
  }

  const coveragePct = Math.round(summary.evaluation_coverage * 100);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-bold text-zinc-200 tracking-wide">Forecast vs Actual Performance</h3>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-zinc-400">Target: <strong className="text-zinc-200">Observed Units Sold</strong></span>
          <span className="text-zinc-600">•</span>
          <span className="text-zinc-400">Coverage: <strong className="text-purple-300">{coveragePct}%</strong> ({summary.evaluated_count}/{summary.eligible_forecast_count})</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* MAE Card */}
        <div className="tactile-card bg-zinc-900/90 border border-zinc-800 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-zinc-400">Mean Absolute Error (MAE)</span>
            <div className="p-1.5 bg-purple-950/60 rounded-lg border border-purple-800/40">
              <Target className="w-3.5 h-3.5 text-purple-300" />
            </div>
          </div>
          <div className="text-2xl font-bold text-zinc-100 mt-2 font-mono">
            {summary.mae !== null && summary.mae !== undefined ? `${summary.mae} pcs` : 'N/A'}
          </div>
          <span className="text-[10px] text-zinc-500 mt-1 block">Average absolute error magnitude</span>
        </div>

        {/* RMSE Card */}
        <div className="tactile-card bg-zinc-900/90 border border-zinc-800 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-zinc-400">Root Mean Sq Error (RMSE)</span>
            <div className="p-1.5 bg-zinc-800 rounded-lg border border-zinc-700">
              <Activity className="w-3.5 h-3.5 text-zinc-300" />
            </div>
          </div>
          <div className="text-2xl font-bold text-zinc-100 mt-2 font-mono">
            {summary.rmse !== null && summary.rmse !== undefined ? `${summary.rmse} pcs` : 'N/A'}
          </div>
          <span className="text-[10px] text-zinc-500 mt-1 block">Penalizes large outlier errors</span>
        </div>

        {/* Zero-Safe MAPE Card */}
        <div className="tactile-card bg-zinc-900/90 border border-zinc-800 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-zinc-400">Zero-Safe MAPE</span>
            <div className="p-1.5 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
              <Percent className="w-3.5 h-3.5 text-emerald-400" />
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2 font-mono">
            {summary.mape !== null && summary.mape !== undefined ? `${summary.mape}%` : 'N/A'}
          </div>
          <span className="text-[10px] text-zinc-500 mt-1 block">Excludes zero-sales dates</span>
        </div>

        {/* Censored Observations Telemetry */}
        <div className="tactile-card bg-zinc-900/90 border border-zinc-800 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-zinc-400">Stockout Censored Days</span>
            <div className="p-1.5 bg-rose-500/10 rounded-lg border border-rose-500/20">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            </div>
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-2 font-mono">
            {summary.confirmed_stockout_count} days
          </div>
          <div className="flex items-center justify-between text-[10px] text-zinc-500 mt-1">
            <span>is_stockout = TRUE</span>
            <span className="text-amber-400">{summary.zero_eod_stock_count} EOD zero</span>
          </div>
        </div>

      </div>
    </div>
  );
};
