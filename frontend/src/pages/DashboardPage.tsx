import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  DollarSign,
  ShoppingBag,
  TrendingUp,
  Package,
  AlertCircle,
  Clock,
  Sparkles,
  UploadCloud,
  CheckCircle2,
  PieChart as PieIcon,
  BarChart3,
  Database,
  Cpu,
  RefreshCw,
  AlertTriangle,
  Layers,
  Target,
  AlertOctagon
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  CartesianGrid
} from 'recharts';
import {
  analyticsApi,
  productsApi,
  forecastsApi,
  forecastEvaluationApi,
  anomaliesApi,
  AnalyticsSummary,
  SalesTrendPoint,
  CategoryBreakdown,
  TopProductItem,
  DataQualityReport,
  LatestForecastResponse,
  SkippedProductInfo,
  ForecastPoint,
  ForecastMetadata,
  ForecastEvaluationSummary,
  ModelMonitoring,
  AnomalyItem
} from '../services/api';
import { AnalyticsFilters } from '../components/AnalyticsFilters';
import { DataQualityCard } from '../components/DataQualityCard';
import { ForecastChart } from '../components/ForecastChart';
import { ForecastSummaryCards } from '../components/ForecastSummaryCards';
import { ForecastMetadataPanel } from '../components/ForecastMetadata';
import { GroupForecastTable } from '../components/ForecastTable';
import { ForecastEvaluationCards } from '../components/ForecastEvaluationCards';
import { ModelMonitoringCard } from '../components/ModelMonitoringCard';
import { AnomaliesTable } from '../components/AnomaliesTable';

const CATEGORY_COLORS = ['#e4e4e7', '#a1a1aa', '#71717a', '#52525b', '#3f3f46', '#27272a'];

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [range, setRange] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [categories, setCategories] = useState<string[]>([]);
  
  // Analytics States
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [trend, setTrend] = useState<SalesTrendPoint[]>([]);
  const [breakdown, setBreakdown] = useState<CategoryBreakdown[]>([]);
  const [topProducts, setTopProducts] = useState<TopProductItem[]>([]);
  const [dataQuality, setDataQuality] = useState<DataQualityReport | null>(null);
  
  // Forecast States
  const [latestForecast, setLatestForecast] = useState<LatestForecastResponse | null>(null);
  const [forecastLoading, setForecastLoading] = useState<boolean>(true);
  const [generatingForecast, setGeneratingForecast] = useState<boolean>(false);
  const [forecastStatus, setForecastStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [forecastError, setForecastError] = useState<string | null>(null);
  const [skippedProducts, setSkippedProducts] = useState<SkippedProductInfo[]>([]);

  // Phase 5 Intelligence States
  const [evalSummary, setEvalSummary] = useState<ForecastEvaluationSummary | null>(null);
  const [modelMonitoring, setModelMonitoring] = useState<ModelMonitoring | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([]);

  // Other loading states
  const [loading, setLoading] = useState<boolean>(true);
  const [seedingSynthetic, setSeedingSynthetic] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    productsApi.listProducts({ limit: 1000 })
      .then((res) => {
        const uniqueCats = Array.from(new Set(res.data.map((p) => p.category).filter(Boolean))) as string[];
        setCategories(uniqueCats);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [range, selectedCategory]);

  useEffect(() => {
    fetchLatestForecastData();
    fetchPhase5Intelligence();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        range,
        category: selectedCategory || undefined
      };

      const [summaryRes, trendRes, breakdownRes, topRes, qualityRes] = await Promise.all([
        analyticsApi.getSummary(params),
        analyticsApi.getSalesTrend(params),
        analyticsApi.getCategoryBreakdown({ range }),
        analyticsApi.getTopProducts({ limit: 5, range }),
        analyticsApi.getDataQuality({ range })
      ]);

      setSummary(summaryRes.data);
      setTrend(trendRes.data);
      setBreakdown(breakdownRes.data);
      setTopProducts(topRes.data);
      setDataQuality(qualityRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load sales analytics.');
    } finally {
      setLoading(false);
    }
  };

  const fetchLatestForecastData = async () => {
    setForecastLoading(true);
    try {
      const res = await forecastsApi.getLatestForecasts();
      setLatestForecast(res.data);
    } catch (err) {
      console.error('Failed to fetch latest forecasts:', err);
    } finally {
      setForecastLoading(false);
    }
  };

  const fetchPhase5Intelligence = async () => {
    try {
      const [evalRes, monRes, anomalyRes] = await Promise.all([
        forecastEvaluationApi.getSummary(),
        forecastEvaluationApi.getModelMonitoring(),
        anomaliesApi.getAnomalies()
      ]);
      setEvalSummary(evalRes.data);
      setModelMonitoring(monRes.data);
      setAnomalies(anomalyRes.data.anomalies || []);
    } catch (err) {
      console.error('Failed to load Phase 5 intelligence:', err);
    }
  };

  const handleGenerateForecast = async () => {
    setGeneratingForecast(true);
    setForecastStatus('loading');
    setForecastError(null);
    setSkippedProducts([]);

    try {
      const res = await forecastsApi.generateForecasts();
      const data = res.data;

      if (data.skipped_products && data.skipped_products.length > 0) {
        setSkippedProducts(data.skipped_products);
      }

      await fetchLatestForecastData();
      await fetchPhase5Intelligence();
      setForecastStatus('success');

      setTimeout(() => {
        setForecastStatus('idle');
      }, 6000);
    } catch (err: any) {
      setForecastStatus('error');
      setForecastError(err.response?.data?.detail || 'Forecast generation failed. Please try again.');
    } finally {
      setGeneratingForecast(false);
    }
  };

  const handleGenerateSynthetic = async () => {
    setSeedingSynthetic(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/sales/generate-synthetic', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('retailmind_token')}`
        }
      });
      if (res.ok) {
        await fetchDashboardData();
        await fetchLatestForecastData();
        await fetchPhase5Intelligence();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSeedingSynthetic(false);
    }
  };

  const aggregateStoreForecast = useMemo(() => {
    if (!latestForecast || !latestForecast.products || latestForecast.products.length === 0) {
      return [];
    }

    const dateMap: Record<string, number> = {};
    latestForecast.products.forEach((group) => {
      group.forecast.forEach((pt) => {
        const d = pt.forecast_date;
        dateMap[d] = (dateMap[d] || 0) + Number(pt.predicted_units);
      });
    });

    const dates = Object.keys(dateMap).sort();
    return dates.map((d) => ({
      forecast_date: d,
      predicted_units: Number(dateMap[d].toFixed(1))
    }));
  }, [latestForecast]);

  const historicalDailyAvg = useMemo(() => {
    if (!trend || trend.length === 0) return 0;
    const totalUnits = trend.reduce((acc, t) => acc + t.units_sold, 0);
    return totalUnits / trend.length;
  }, [trend]);

  const forecastMeta: ForecastMetadata | null = useMemo(() => {
    if (!latestForecast || latestForecast.total_products === 0) return null;
    return {
      model_name: 'XGBoost',
      model_version: latestForecast.model_version || 'xgb-v1',
      training_cutoff_date: latestForecast.training_cutoff_date || '2025-12-31',
      generated_at: latestForecast.generated_at,
      horizon_days: latestForecast.horizon_days || 7,
      disclaimer: 'Forecasts estimate future observed units sold from historical observations. Stockout-censored demand has not been reconstructed.',
      historical_stockout_ratio: 0.0
    };
  }, [latestForecast]);

  return (
    <div className="page-data-wipe space-y-8 pb-12">
      
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Sales & Operational Intelligence
          </h1>
          <p className="text-zinc-400 text-xs sm:text-sm mt-1">
            Historical analytics, 7-day ML forecasting, forecast evaluation, model drift, and sales anomaly detection
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/import')}
            className="tactile-button flex items-center gap-2 px-4 py-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 rounded-xl text-xs font-semibold border border-zinc-800 transition-all shadow-sm"
          >
            <UploadCloud className="w-4 h-4 text-zinc-300" /> Upload CSV
          </button>
          <button
            onClick={handleGenerateSynthetic}
            disabled={seedingSynthetic}
            className="tactile-button flex items-center gap-2 px-4 py-2 bg-zinc-100 hover:bg-white text-zinc-950 rounded-xl text-xs font-bold transition-all shadow-md disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-purple-600" /> {seedingSynthetic ? 'Seeding...' : 'Seed 7,300 Dataset'}
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <AnalyticsFilters
        range={range}
        onRangeChange={setRange}
        selectedCategory={selectedCategory}
        onCategoryChange={setSelectedCategory}
        categories={categories}
      />

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-center gap-3 text-rose-400 text-xs">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Executive KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <div className="tactile-card bg-zinc-900/80 rounded-2xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-zinc-400">Total Revenue</span>
            <div className="p-2 bg-zinc-800 rounded-xl border border-zinc-700/80">
              <DollarSign className="w-4 h-4 text-zinc-200" />
            </div>
          </div>
          <div className={`text-xl font-bold text-zinc-100 mt-3 font-mono ${loading ? 'skeleton-acquisition h-7 w-28 rounded-lg' : 'animate-inventory-pulse'}`}>
            {!loading && summary && `₹${Number(summary.total_revenue).toLocaleString('en-IN')}`}
          </div>
          <span className="text-[10px] text-zinc-500 mt-1 block">In selected date range</span>
        </div>

        <div className="tactile-card bg-zinc-900/80 rounded-2xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-zinc-400">Observed Units Sold</span>
            <div className="p-2 bg-zinc-800 rounded-xl border border-zinc-700/80">
              <ShoppingBag className="w-4 h-4 text-zinc-200" />
            </div>
          </div>
          <div className={`text-xl font-bold text-zinc-100 mt-3 font-mono ${loading ? 'skeleton-acquisition h-7 w-24 rounded-lg' : 'animate-inventory-pulse'}`}>
            {!loading && summary && `${summary.observed_units_sold.toLocaleString('en-IN')} pcs`}
          </div>
          <span className="text-[10px] text-zinc-500 mt-1 block">Historical aggregate</span>
        </div>

        <div className="tactile-card bg-zinc-900/80 rounded-2xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-zinc-400">Avg Revenue / Day</span>
            <div className="p-2 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            </div>
          </div>
          <div className={`text-xl font-bold text-emerald-400 mt-3 font-mono ${loading ? 'skeleton-acquisition h-7 w-28 rounded-lg' : 'animate-inventory-pulse'}`}>
            {!loading && summary && `₹${Number(summary.avg_revenue_per_recorded_day).toLocaleString('en-IN')}`}
          </div>
          <span className="text-[10px] text-zinc-500 mt-1 block">Distinct sale dates</span>
        </div>

        <div className="tactile-card bg-zinc-900/80 rounded-2xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-zinc-400">Active Catalog</span>
            <div className="p-2 bg-zinc-800 rounded-xl border border-zinc-700/80">
              <Package className="w-4 h-4 text-zinc-200" />
            </div>
          </div>
          <div className={`text-xl font-bold text-zinc-100 mt-3 font-mono ${loading ? 'skeleton-acquisition h-7 w-20 rounded-lg' : 'animate-inventory-pulse'}`}>
            {!loading && summary && `${summary.active_catalog_size} items`}
          </div>
          <span className="text-[10px] text-zinc-500 mt-1 block">Active products</span>
        </div>

        <div className="tactile-card bg-zinc-900/80 rounded-2xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-zinc-400">Confirmed Stockouts</span>
            <div className="p-2 bg-rose-500/10 rounded-xl border border-rose-500/20">
              <AlertCircle className="w-4 h-4 text-rose-400" />
            </div>
          </div>
          <div className={`text-xl font-bold text-rose-400 mt-3 font-mono ${loading ? 'skeleton-acquisition h-7 w-20 rounded-lg' : 'animate-inventory-pulse'}`}>
            {!loading && summary && `${summary.confirmed_stockout_days} days`}
          </div>
          <span className="text-[10px] text-zinc-500 mt-1 block">is_stockout = TRUE</span>
        </div>

        <div className="tactile-card bg-zinc-900/80 rounded-2xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-zinc-400">Zero EOD Stock Days</span>
            <div className="p-2 bg-amber-500/10 rounded-xl border border-amber-500/20">
              <Clock className="w-4 h-4 text-amber-400" />
            </div>
          </div>
          <div className={`text-xl font-bold text-amber-400 mt-3 font-mono ${loading ? 'skeleton-acquisition h-7 w-20 rounded-lg' : 'animate-inventory-pulse'}`}>
            {!loading && summary && `${summary.zero_eod_stock_days} days`}
          </div>
          <span className="text-[10px] text-zinc-500 mt-1 block">stock_available = 0</span>
        </div>
      </div>

      {/* Data Quality Indicator Card */}
      <DataQualityCard report={dataQuality} />

      {/* DEMAND FORECAST SECTION */}
      <div className="bg-[#121215] border border-purple-950/80 rounded-2xl p-6 shadow-2xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-purple-900/30 pb-5">
          <div className="space-y-1">
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              DEMAND FORECAST
            </h2>
            <p className="text-xs sm:text-sm text-[#a1a1aa]">
              7-day observed-sales forecast generated from leakage-safe temporal features and XGBoost tabular regression
            </p>

            {latestForecast && (
              <div className="flex flex-wrap items-center gap-3 pt-2 text-xs font-mono">
                <span className="text-zinc-400">Model: <strong className="text-purple-300">XGBoost</strong></span>
                <span className="text-zinc-600">•</span>
                <span className="text-zinc-400">Version: <strong className="text-purple-300">{latestForecast.model_version || 'xgb-v1'}</strong></span>
                <span className="text-zinc-600">•</span>
                <span className="text-zinc-400">Training cutoff: <strong className="text-zinc-200">{latestForecast.training_cutoff_date || '31 Dec 2025'}</strong></span>
              </div>
            )}
          </div>

          <div>
            <button
              onClick={handleGenerateForecast}
              disabled={generatingForecast}
              className="tactile-button flex items-center gap-2.5 px-5 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-purple-950/50 disabled:opacity-50"
            >
              {generatingForecast ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  Generating Forecast...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-purple-200" />
                  Generate 7-Day Forecast
                </>
              )}
            </button>
          </div>
        </div>

        {forecastStatus === 'success' && (
          <div className="bg-emerald-950/40 border border-emerald-800/60 rounded-xl p-3.5 flex items-center gap-3 text-emerald-300 text-xs animate-inventory-pulse">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="font-semibold">Forecast updated successfully! 7-day predictions persisted to database.</span>
          </div>
        )}

        {forecastStatus === 'error' && (
          <div className="bg-rose-950/40 border border-rose-800/60 rounded-xl p-3.5 flex items-center justify-between gap-3 text-rose-300 text-xs">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>Forecast unavailable: {forecastError}</span>
            </div>
            <button
              onClick={handleGenerateForecast}
              className="px-3 py-1 bg-rose-900/80 hover:bg-rose-800 text-rose-100 rounded-lg font-semibold text-[11px]"
            >
              Retry
            </button>
          </div>
        )}

        {skippedProducts.length > 0 && (
          <div className="bg-amber-950/30 border border-amber-800/50 rounded-xl p-4 text-xs space-y-2">
            <div className="flex items-center gap-2 text-amber-300 font-semibold">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>{skippedProducts.length} Product(s) Skipped during Forecast Generation</span>
            </div>
            <p className="text-amber-200/80 text-[11px]">
              Reason: <strong>INSUFFICIENT_HISTORY</strong> (&lt; 28 recorded sales dates available for model features).
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              {skippedProducts.map((p) => (
                <span key={p.product_id} className="px-2 py-0.5 rounded bg-amber-900/40 border border-amber-800/40 text-amber-300 text-[11px] font-mono">
                  {p.name || `Product #${p.product_id}`} ({p.sku || 'SKU'})
                </span>
              ))}
            </div>
          </div>
        )}

        {forecastLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton-acquisition h-24 rounded-xl" />
            ))}
          </div>
        ) : (
          <ForecastSummaryCards
            forecastPoints={aggregateStoreForecast}
            historicalDailyAvg={historicalDailyAvg}
          />
        )}

        {forecastLoading ? (
          <div className="skeleton-acquisition h-80 rounded-xl w-full" />
        ) : (
          <ForecastChart
            historicalData={trend}
            forecastData={aggregateStoreForecast}
            modelName="XGBoost"
            modelVersion={latestForecast?.model_version || 'xgb-v1'}
          />
        )}

        {forecastMeta && <ForecastMetadataPanel metadata={forecastMeta} />}

        {!forecastLoading && latestForecast && (
          <GroupForecastTable
            groups={latestForecast.products || []}
            onSelectProduct={(pid) => navigate(`/products/${pid}`)}
          />
        )}
      </div>

      {/* ================================================================== */}
      {/* PHASE 5 — OPERATIONAL INTELLIGENCE PANELS */}
      {/* ================================================================== */}
      <div className="space-y-6">
        
        {/* SECTION 1: FORECAST PERFORMANCE */}
        <ForecastEvaluationCards summary={evalSummary} />

        {/* SECTION 2: MODEL DRIFT & MONITORING */}
        <ModelMonitoringCard monitoring={modelMonitoring} />

        {/* SECTION 3: SALES & DEMAND ANOMALIES */}
        <AnomaliesTable
          anomalies={anomalies}
          categories={categories}
          onSelectProduct={(pid) => navigate(`/products/${pid}`)}
          onFilterChange={(filters) => {
            anomaliesApi.getAnomalies(filters)
              .then((res) => setAnomalies(res.data.anomalies || []))
              .catch(() => {});
          }}
        />

      </div>

      {/* Visualizations Section (Sales Trend & Category Share) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-zinc-900/80 border border-zinc-800 rounded-2xl p-5 shadow-xl backdrop-blur-md">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-zinc-300" />
              <h3 className="text-sm font-bold text-zinc-200 tracking-wide">Historical Revenue Trajectory</h3>
            </div>
            <span className="text-xs text-zinc-400 font-mono">Recorded Store Transactions</span>
          </div>

          <div className="h-72 w-full animate-demand-flow">
            {trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trend} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#e4e4e7" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#e4e4e7" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" opacity={0.6} />
                  <XAxis dataKey="sale_date" stroke="#71717a" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#71717a" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#3f3f46', borderRadius: '12px', fontSize: '12px' }}
                    formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')}`, 'Revenue']}
                  />
                  <Area
                    type="monotone"
                    dataKey="revenue"
                    stroke="#e4e4e7"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#revenueGrad)"
                    isAnimationActive={true}
                    animationDuration={850}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-data-grid h-full rounded-xl border border-zinc-800/80 flex flex-col items-center justify-center text-zinc-400 p-6 text-center">
                <Database className="w-8 h-8 text-zinc-500 mb-2" />
                <span className="text-xs font-semibold text-zinc-300">No data loaded</span>
                <span className="text-[11px] text-zinc-500 mt-1">Upload a sales CSV or seed synthetic data</span>
              </div>
            )}
          </div>
        </div>

        <div className="bg-zinc-900/80 border border-zinc-800 rounded-2xl p-5 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <PieIcon className="w-5 h-5 text-zinc-300" />
              <h3 className="text-sm font-bold text-zinc-200 tracking-wide">Category Revenue Share</h3>
            </div>

            <div className="h-52 w-full flex items-center justify-center animate-category-resolve">
              {breakdown.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={breakdown}
                      dataKey="revenue"
                      nameKey="category"
                      cx="50%"
                      cy="50%"
                      innerRadius={52}
                      outerRadius={78}
                      paddingAngle={3}
                      isAnimationActive={true}
                      animationDuration={600}
                    >
                      {breakdown.map((_, idx) => (
                        <Cell key={`cell-${idx}`} fill={CATEGORY_COLORS[idx % CATEGORY_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#18181b', borderColor: '#3f3f46', borderRadius: '12px', fontSize: '12px' }}
                      formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')}`, 'Revenue']}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-data-grid w-full h-full rounded-xl border border-zinc-800/80 flex flex-col items-center justify-center text-zinc-400 p-4 text-center">
                  <span className="text-xs font-medium text-zinc-500">No category breakdown</span>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-2 mt-2">
            {breakdown.slice(0, 4).map((cat, idx) => (
              <div key={cat.category} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }} />
                  <span className="text-zinc-300 font-medium">{cat.category}</span>
                </div>
                <span className="font-bold text-zinc-200 font-mono">{cat.percentage_share}%</span>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Top 5 Performing Products Table */}
      <div className="bg-zinc-900/80 border border-zinc-800 rounded-2xl p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <h3 className="text-sm font-bold text-zinc-200 tracking-wide">Top Performing Products</h3>
          </div>
          <button
            onClick={() => navigate('/products')}
            className="tactile-button text-xs font-semibold text-zinc-300 hover:text-white transition-colors"
          >
            View All Catalog →
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-zinc-400 border-b border-zinc-800 bg-zinc-950/80">
                <th className="py-3 px-4 font-semibold">SKU</th>
                <th className="py-3 px-4 font-semibold">Product Name</th>
                <th className="py-3 px-4 font-semibold">Category</th>
                <th className="py-3 px-4 font-semibold">Observed Units Sold</th>
                <th className="py-3 px-4 font-semibold text-right">Total Revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {topProducts.map((p, idx) => {
                const batchClass = idx < 2 ? 'materialize-batch-1' : (idx < 4 ? 'materialize-batch-2' : 'materialize-batch-3');
                return (
                  <tr key={p.product_id} className={`${batchClass} hover:bg-zinc-800/40 transition-colors`}>
                    <td className="py-3 px-4 font-mono font-semibold text-zinc-200">{p.sku}</td>
                    <td className="py-3 px-4 font-medium text-zinc-200">{p.name}</td>
                    <td className="py-3 px-4 text-zinc-400">{p.category || 'General'}</td>
                    <td className="py-3 px-4 text-zinc-300 font-semibold font-mono">{p.total_units_sold.toLocaleString()} pcs</td>
                    <td className="py-3 px-4 font-bold text-right text-emerald-400 font-mono">₹{Number(p.total_revenue).toLocaleString('en-IN')}</td>
                  </tr>
                );
              })}
              {topProducts.length === 0 && !loading && (
                <tr>
                  <td colSpan={5} className="py-8 text-center">
                    <div className="empty-data-grid py-8 rounded-xl border border-zinc-800/80 flex flex-col items-center justify-center text-zinc-400">
                      <Database className="w-6 h-6 text-zinc-500 mb-1.5" />
                      <span className="text-xs font-semibold text-zinc-300">No data loaded</span>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
