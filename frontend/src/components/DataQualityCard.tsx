import React from 'react';
import { ShieldCheck, AlertTriangle, Activity, Calendar, Info } from 'lucide-react';
import { DataQualityReport } from '../services/api';

interface DataQualityCardProps {
  report: DataQualityReport | null;
}

export const DataQualityCard: React.FC<DataQualityCardProps> = ({ report }) => {
  if (!report) return null;

  const getBadgeColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'excellent':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'good':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      case 'warning':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      default:
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
    }
  };

  return (
    <div className="data-scan-line bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md relative overflow-hidden">
      
      <div className="flex items-center justify-between mb-4 relative z-10">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-bold text-slate-200 tracking-wide">Data Integrity & Quality Score</h3>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getBadgeColor(report.status)}`}>
          {report.status} ({report.quality_score}%)
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 relative z-10">
        
        {/* Quality Score Bar */}
        <div className="bg-slate-950/80 rounded-xl p-3.5 border border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-400 mb-1 flex items-center justify-between">
            <span>Overall Score</span>
            <span className="font-bold text-slate-200 font-mono">{report.quality_score}%</span>
          </div>
          <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full rounded-full transition-all duration-700 ease-out"
              style={{ width: `${Math.min(100, Math.max(0, report.quality_score))}%` }}
            />
          </div>
          <span className="text-[10px] text-slate-500 mt-1 block">Based on completeness & coverage</span>
        </div>

        {/* Date Coverage */}
        <div className="bg-slate-950/80 rounded-xl p-3.5 border border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-400 mb-1 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-cyan-400" /> Date Coverage
          </div>
          <div className="text-lg font-bold text-slate-100 font-mono">
            {report.total_recorded_days} <span className="text-xs font-normal text-slate-400">/ {report.expected_days} days</span>
          </div>
          <span className="text-[10px] text-slate-400 mt-0.5 block font-mono">
            {(report.date_coverage_ratio * 100).toFixed(1)}% Continuity Ratio
          </span>
        </div>

        {/* Date Gaps Count */}
        <div className="bg-slate-950/80 rounded-xl p-3.5 border border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-400 mb-1 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Missing Date Gaps
          </div>
          <div className="text-lg font-bold text-amber-400 font-mono">
            {report.date_gaps_count} <span className="text-xs font-normal text-slate-400">gaps</span>
          </div>
          <span className="text-[10px] text-slate-500 mt-0.5 block">Unrecorded calendar dates</span>
        </div>

        {/* Operational Stockout Censoring Ratio */}
        <div className="bg-slate-950/80 rounded-xl p-3.5 border border-slate-800/80">
          <div className="text-[11px] font-medium text-slate-400 mb-1 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-purple-400" /> Stockout Censoring
          </div>
          <div className="text-lg font-bold text-purple-400 font-mono">
            {(report.stockout_censored_ratio * 100).toFixed(1)}%
          </div>
          <div className="flex items-center gap-1 text-[10px] text-slate-400 mt-0.5" title="Operational business indicator, not bad data">
            <Info className="w-3 h-3 text-slate-500" />
            <span>Operational Indicator</span>
          </div>
        </div>

      </div>
    </div>
  );
};
