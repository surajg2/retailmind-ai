import React from 'react';
import { Cpu, AlertTriangle, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';
import { ModelMonitoring } from '../services/api';

interface ModelMonitoringCardProps {
  monitoring: ModelMonitoring | null;
}

export const ModelMonitoringCard: React.FC<ModelMonitoringCardProps> = ({ monitoring }) => {
  if (!monitoring) return null;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'STABLE':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 font-mono">
            <CheckCircle2 className="w-3.5 h-3.5" /> STABLE
          </span>
        );
      case 'WATCH':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1.5 font-mono">
            <AlertTriangle className="w-3.5 h-3.5" /> WATCH
          </span>
        );
      case 'DEGRADED':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1.5 font-mono">
            <AlertCircle className="w-3.5 h-3.5" /> DEGRADED
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-zinc-800 text-zinc-400 border border-zinc-700 flex items-center gap-1.5 font-mono">
            <HelpCircle className="w-3.5 h-3.5" /> INSUFFICIENT DATA
          </span>
        );
    }
  };

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-xl p-5 shadow-lg backdrop-blur-sm space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-zinc-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-purple-950/60 rounded-xl border border-purple-800/40">
            <Cpu className="w-4 h-4 text-purple-300" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-zinc-200">Forecast Drift & Performance Monitoring</h3>
            <p className="text-[11px] text-zinc-400 font-mono">
              Engine: {monitoring.model_name} ({monitoring.model_version})
            </p>
          </div>
        </div>

        {getStatusBadge(monitoring.status)}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
        <div className="bg-zinc-950/60 p-3 rounded-lg border border-zinc-800/80">
          <span className="text-zinc-500 text-[10px] uppercase font-sans block">Recent MAE (Last 7 Days)</span>
          <span className="text-sm font-bold text-zinc-200 mt-1 block">
            {monitoring.recent_mae !== null && monitoring.recent_mae !== undefined ? `${monitoring.recent_mae} pcs` : 'N/A'}
          </span>
        </div>

        <div className="bg-zinc-950/60 p-3 rounded-lg border border-zinc-800/80">
          <span className="text-zinc-500 text-[10px] uppercase font-sans block">Historical Baseline MAE</span>
          <span className="text-sm font-bold text-zinc-300 mt-1 block">
            {monitoring.historical_mae !== null && monitoring.historical_mae !== undefined ? `${monitoring.historical_mae} pcs` : 'N/A'}
          </span>
        </div>

        <div className="bg-zinc-950/60 p-3 rounded-lg border border-zinc-800/80">
          <span className="text-zinc-500 text-[10px] uppercase font-sans block">Degradation Ratio</span>
          <span className={`text-sm font-bold mt-1 block ${
            monitoring.status === 'DEGRADED' ? 'text-rose-400' : (monitoring.status === 'WATCH' ? 'text-amber-400' : 'text-emerald-400')
          }`}>
            {monitoring.degradation_ratio !== null && monitoring.degradation_ratio !== undefined ? `${monitoring.degradation_ratio}x` : 'N/A'}
          </span>
        </div>
      </div>

      <p className="text-xs text-zinc-400 bg-zinc-950/40 p-3 rounded-lg border border-zinc-800/60 leading-relaxed">
        {monitoring.explanation}
      </p>
    </div>
  );
};
