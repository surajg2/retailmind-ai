import React from 'react';
import { Cpu, ShieldCheck, Clock, AlertTriangle, Info, Layers } from 'lucide-react';
import { ForecastMetadata as MetadataType } from '../services/api';

interface ForecastMetadataProps {
  metadata: MetadataType;
  className?: string;
}

export const ForecastMetadataPanel: React.FC<ForecastMetadataProps> = ({ metadata, className = '' }) => {
  if (!metadata) return null;

  // Calculate relative freshness
  const getFreshness = () => {
    try {
      const genDate = new Date(metadata.generated_at);
      const now = new Date();
      const diffMs = now.getTime() - genDate.getTime();
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      const diffHours = Math.floor(diffMinutes / 60);

      const isStale = diffHours >= 24;

      let timeText = 'Just now';
      if (diffMinutes >= 1 && diffMinutes < 60) {
        timeText = `${diffMinutes} min ago`;
      } else if (diffHours >= 1 && diffHours < 24) {
        timeText = `${diffHours} hr${diffHours > 1 ? 's' : ''} ago`;
      } else if (diffHours >= 24) {
        const days = Math.floor(diffHours / 24);
        timeText = `${days} day${days > 1 ? 's' : ''} ago`;
      }

      return { timeText, isStale };
    } catch {
      return { timeText: 'Unknown', isStale: false };
    }
  };

  const { timeText, isStale } = getFreshness();

  // Format cutoff date
  const formatCutoff = (str: string) => {
    try {
      return new Date(str).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch {
      return str;
    }
  };

  // Format generated date
  const formatGeneratedAt = (str: string) => {
    try {
      return new Date(str).toLocaleString('en-US', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return str;
    }
  };

  const stockoutRatioPct = metadata.historical_stockout_ratio !== undefined && metadata.historical_stockout_ratio !== null
    ? `${(Number(metadata.historical_stockout_ratio) * 100).toFixed(1)}%`
    : '0.0%';

  return (
    <div className={`bg-[#18181b] border border-[#27272a] rounded-xl p-4 space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#27272a] pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded bg-purple-950/80 text-purple-400 border border-purple-800/60">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-[#f4f4f5] tracking-wide uppercase">Model Telemetry & Metadata</h4>
            <p className="text-[11px] text-[#a1a1aa]">Technical specification of active demand model</p>
          </div>
        </div>

        {/* Freshness Badge */}
        <div className="flex items-center gap-2 text-xs">
          {isStale ? (
            <span className="px-2.5 py-1 rounded-md bg-amber-950/80 border border-amber-800 text-amber-300 font-medium flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              Forecast may be stale ({timeText})
            </span>
          ) : (
            <span className="px-2.5 py-1 rounded-md bg-zinc-800/80 border border-zinc-700 text-zinc-300 font-medium flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-purple-400" />
              Generated {timeText}
            </span>
          )}
        </div>
      </div>

      {/* Metadata Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
        <div className="bg-[#09090b] p-2.5 rounded-lg border border-[#27272a]">
          <span className="text-[#a1a1aa] block text-[10px] uppercase font-medium">Model Engine</span>
          <span className="font-semibold text-[#f4f4f5] mt-0.5 block">{metadata.model_name || 'XGBoost'}</span>
        </div>

        <div className="bg-[#09090b] p-2.5 rounded-lg border border-[#27272a]">
          <span className="text-[#a1a1aa] block text-[10px] uppercase font-medium">Model Version</span>
          <span className="font-mono font-semibold text-purple-300 mt-0.5 block">{metadata.model_version || 'xgb-v1'}</span>
        </div>

        <div className="bg-[#09090b] p-2.5 rounded-lg border border-[#27272a]">
          <span className="text-[#a1a1aa] block text-[10px] uppercase font-medium">Training Cutoff</span>
          <span className="font-medium text-[#f4f4f5] mt-0.5 block">{formatCutoff(metadata.training_cutoff_date)}</span>
        </div>

        <div className="bg-[#09090b] p-2.5 rounded-lg border border-[#27272a]">
          <span className="text-[#a1a1aa] block text-[10px] uppercase font-medium">Forecast Horizon</span>
          <span className="font-medium text-[#f4f4f5] mt-0.5 block">{metadata.horizon_days || 7} Days</span>
        </div>

        <div className="bg-[#09090b] p-2.5 rounded-lg border border-[#27272a]">
          <span className="text-[#a1a1aa] block text-[10px] uppercase font-medium">Generated At</span>
          <span className="font-medium text-[#f4f4f5] mt-0.5 block truncate" title={metadata.generated_at}>
            {formatGeneratedAt(metadata.generated_at)}
          </span>
        </div>

        <div className="bg-[#09090b] p-2.5 rounded-lg border border-[#27272a]">
          <span className="text-[#a1a1aa] block text-[10px] uppercase font-medium">Hist. Stockout Ratio</span>
          <span className="font-mono font-medium text-amber-300 mt-0.5 block">{stockoutRatioPct}</span>
        </div>
      </div>

      {/* Mandatory Disclaimer */}
      <div className="bg-purple-950/20 border border-purple-900/40 rounded-lg p-3 flex items-start gap-2.5 text-xs text-purple-200/90">
        <Info className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          {metadata.disclaimer ||
            'Forecasts estimate future observed units sold from historical observations. Stockout-censored demand has not been reconstructed.'}
        </p>
      </div>
    </div>
  );
};
