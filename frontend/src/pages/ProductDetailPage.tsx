import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Package,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Calendar,
  Activity,
  Sparkles,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import {
  productsApi,
  analyticsApi,
  forecastsApi,
  ProductItem,
  ProductPerformancePoint,
  ProductForecastResponse,
  ForecastPoint
} from '../services/api';
import { ForecastChart } from '../components/ForecastChart';
import { SingleProductForecastTable } from '../components/ForecastTable';
import { ForecastSummaryCards } from '../components/ForecastSummaryCards';

export const ProductDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const productId = Number(id);

  const [product, setProduct] = useState<ProductItem | null>(null);
  const [performance, setPerformance] = useState<ProductPerformancePoint[]>([]);
  const [productForecast, setProductForecast] = useState<ProductForecastResponse | null>(null);
  
  const [range, setRange] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);
  const [forecastLoading, setForecastLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!productId) return;
    fetchProductDetails();
    fetchProductForecast();
  }, [productId, range]);

  const fetchProductDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const [prodRes, perfRes] = await Promise.all([
        productsApi.getProduct(productId),
        analyticsApi.getProductPerformance(productId, { range })
      ]);
      setProduct(prodRes.data);
      setPerformance(perfRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load product details.');
    } finally {
      setLoading(false);
    }
  };

  const fetchProductForecast = async () => {
    setForecastLoading(true);
    try {
      const res = await forecastsApi.getProductForecast(productId);
      setProductForecast(res.data);
    } catch (err) {
      console.log('No existing forecast for product or error:', err);
      setProductForecast(null);
    } finally {
      setForecastLoading(false);
    }
  };

  const handleGenerateProductForecast = async () => {
    setGenerating(true);
    try {
      await forecastsApi.generateForecasts(productId);
      await fetchProductForecast();
    } catch (err: any) {
      console.error('Failed to generate product forecast:', err);
    } finally {
      setGenerating(false);
    }
  };

  // Convert performance points to historical points format for ForecastChart
  const historicalChartPoints = useMemo(() => {
    return performance.map((p) => ({
      sale_date: p.sale_date,
      units_sold: p.units_sold
    }));
  }, [performance]);

  // Compute historical daily average for summary cards
  const historicalDailyAvg = useMemo(() => {
    if (!performance || performance.length === 0) return 0;
    const totalUnits = performance.reduce((acc, p) => acc + p.units_sold, 0);
    return totalUnits / performance.length;
  }, [performance]);

  if (loading) {
    return (
      <div className="page-data-wipe p-8 text-center space-y-4">
        <div className="skeleton-acquisition h-12 w-64 mx-auto rounded-xl" />
        <div className="skeleton-acquisition h-64 max-w-4xl mx-auto rounded-2xl" />
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="page-data-wipe p-8 text-center space-y-4">
        <div className="text-rose-400 font-medium text-sm">{error || 'Product not found.'}</div>
        <button
          onClick={() => navigate('/products')}
          className="tactile-button px-4 py-2 bg-zinc-800 text-zinc-300 rounded-xl text-xs font-semibold hover:bg-zinc-700"
        >
          ← Back to Products Catalog
        </button>
      </div>
    );
  }

  const totalUnits = performance.reduce((acc, curr) => acc + curr.units_sold, 0);
  const confirmedStockoutDays = performance.filter((p) => p.is_stockout === true).length;
  const zeroStockDays = performance.filter((p) => p.stock_available === 0).length;

  return (
    <div className="page-data-wipe space-y-8 pb-12">
      
      {/* Back Button & Header */}
      <div>
        <button
          onClick={() => navigate('/products')}
          className="tactile-button inline-flex items-center gap-2 text-xs font-semibold text-zinc-300 hover:text-white transition-colors mb-3"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Products Catalog
        </button>

        <div className="tactile-card bg-zinc-900/80 border border-zinc-800 rounded-2xl p-6 shadow-xl backdrop-blur-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs font-bold text-zinc-200 bg-zinc-800 px-2.5 py-1 rounded-lg border border-zinc-700">
                {product.sku}
              </span>
              <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">{product.name}</h1>
              {product.is_active ? (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Active Catalog
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  Soft Deactivated
                </span>
              )}
            </div>
            <p className="text-zinc-400 text-xs mt-1.5">
              Category: <span className="text-zinc-200 font-medium">{product.category || 'General'}</span> | Unit: <span className="text-zinc-200 font-medium">{product.unit}</span>
            </p>
          </div>

          <div className="flex items-center gap-6 font-mono">
            <div>
              <span className="text-[10px] font-semibold text-zinc-400 block font-sans">Selling Price</span>
              <span className="text-lg font-bold text-emerald-400">₹{Number(product.selling_price).toFixed(2)}</span>
            </div>
            <div>
              <span className="text-[10px] font-semibold text-zinc-400 block font-sans">Cost Price</span>
              <span className="text-lg font-bold text-zinc-300">₹{Number(product.cost_price).toFixed(2)}</span>
            </div>
            <div>
              <span className="text-[10px] font-semibold text-zinc-400 block font-sans">Min Stock Threshold</span>
              <span className="text-lg font-bold text-zinc-200">{product.min_stock_level} {product.unit}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ================================================================== */}
      {/* 7-DAY DEMAND FORECAST SECTION */}
      {/* ================================================================== */}
      <div className="bg-[#121215] border border-purple-950/80 rounded-2xl p-6 shadow-2xl space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-purple-900/30 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-purple-950 text-purple-300 border border-purple-800/80 flex items-center gap-1.5">
                <Sparkles className="w-3 h-3 text-purple-400" />
                Product AI Intelligence
              </span>
              <span className="text-xs text-zinc-500 font-mono">XGBoost v1.0</span>
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight mt-1">
              7-DAY DEMAND FORECAST
            </h2>
            <p className="text-xs text-[#a1a1aa]">
              Product-level predicted observed units sold for next 7 calendar days
            </p>
          </div>

          <button
            onClick={handleGenerateProductForecast}
            disabled={generating}
            className="tactile-button flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold transition-all shadow-md disabled:opacity-50"
          >
            {generating ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-purple-200" />
                Generate Product Forecast
              </>
            )}
          </button>
        </div>

        {/* Product Forecast Summary Cards */}
        {productForecast && productForecast.forecast.length > 0 && (
          <ForecastSummaryCards
            forecastPoints={productForecast.forecast}
            historicalDailyAvg={historicalDailyAvg}
          />
        )}

        {/* Product Forecast Chart */}
        {!forecastLoading && productForecast ? (
          <ForecastChart
            historicalData={historicalChartPoints}
            forecastData={productForecast.forecast}
            modelName={productForecast.metadata.model_name}
            modelVersion={productForecast.metadata.model_version}
          />
        ) : (
          <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-8 text-center text-[#a1a1aa] empty-data-grid">
            <Sparkles className="w-6 h-6 mx-auto mb-2 text-zinc-600" />
            <p className="text-sm font-medium text-[#f4f4f5]">No 7-day forecast generated for this product</p>
            <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
              Click &quot;Generate Product Forecast&quot; to run XGBoost predictions using this product&apos;s historical sales features.
            </p>
          </div>
        )}

        {/* Product Forecast Table */}
        {productForecast && productForecast.forecast.length > 0 && (
          <SingleProductForecastTable
            forecastPoints={productForecast.forecast}
            modelName={`${productForecast.metadata.model_name} (${productForecast.metadata.model_version})`}
          />
        )}
      </div>

      {/* Range Preset Selector */}
      <div className="flex items-center justify-between bg-zinc-900/80 border border-zinc-800 rounded-xl p-3 backdrop-blur-sm">
        <span className="text-xs font-semibold text-zinc-400 flex items-center gap-1">
          <Calendar className="w-3.5 h-3.5 text-zinc-300" /> Historical Performance Timeframe:
        </span>
        <div className="flex items-center gap-1.5">
          {['7d', '30d', '90d', '1y', 'all'].map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`tactile-button px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                range === r
                  ? 'bg-zinc-100 text-zinc-950 font-bold shadow-md'
                  : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'
              }`}
            >
              {r.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="tactile-card bg-zinc-900/80 rounded-2xl p-4 backdrop-blur-sm">
          <span className="text-[11px] font-semibold text-zinc-400">Observed Units Sold</span>
          <div className="text-2xl font-bold text-zinc-100 mt-2 font-mono animate-inventory-pulse">{totalUnits.toLocaleString()} pcs</div>
          <span className="text-[10px] text-zinc-500 mt-1 block">In selected timeframe</span>
        </div>

        {/* Confirmed Stockouts */}
        <div className="tactile-card bg-zinc-900/80 rounded-2xl p-4 backdrop-blur-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-zinc-400">Confirmed Stockout Days</span>
            {confirmedStockoutDays > 0 && (
              <div className="stockout-dot-container w-3 h-3">
                <span className="stockout-ripple" />
                <span className="w-2 h-2 rounded-full bg-rose-500" />
              </div>
            )}
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-2 font-mono animate-inventory-pulse">{confirmedStockoutDays} days</div>
          <span className="text-[10px] text-zinc-500 mt-1 block">is_stockout = TRUE</span>
        </div>

        <div className="tactile-card bg-zinc-900/80 rounded-2xl p-4 backdrop-blur-sm">
          <span className="text-[11px] font-semibold text-zinc-400">Zero EOD Inventory Days</span>
          <div className="text-2xl font-bold text-amber-400 mt-2 font-mono animate-inventory-pulse">{zeroStockDays} days</div>
          <span className="text-[10px] text-zinc-500 mt-1 block">stock_available = 0</span>
        </div>
      </div>

      {/* Composed Performance Timeline Chart */}
      <div className="bg-zinc-900/80 border border-zinc-800 rounded-2xl p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-zinc-300" />
            <h3 className="text-sm font-bold text-zinc-200 tracking-wide">Daily Observed Sales & Inventory Trajectory</h3>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5 text-zinc-300 font-medium">
              <span className="w-3 h-3 bg-zinc-300 rounded-sm inline-block" /> Observed Units Sold
            </span>
            <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <span className="w-3 h-0.5 bg-emerald-400 inline-block" /> Ending Inventory
            </span>
          </div>
        </div>

        <div className="h-80 w-full animate-demand-flow">
          {performance.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={performance} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" opacity={0.6} />
                <XAxis dataKey="sale_date" stroke="#71717a" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" stroke="#e4e4e7" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" stroke="#10b981" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#18181b', borderColor: '#3f3f46', borderRadius: '12px', fontSize: '12px' }}
                />
                <Bar yAxisId="left" dataKey="units_sold" name="Observed Units Sold" fill="#a1a1aa" radius={[4, 4, 0, 0]} isAnimationActive={true} animationDuration={850} />
                <Line yAxisId="right" type="monotone" dataKey="stock_available" name="Ending Inventory" stroke="#10b981" strokeWidth={2} dot={false} isAnimationActive={true} animationDuration={850} />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-data-grid h-full rounded-xl border border-zinc-800/80 flex items-center justify-center text-zinc-500 text-xs">
              No historical records for this product in timeframe.
            </div>
          )}
        </div>
      </div>

    </div>
  );
};
