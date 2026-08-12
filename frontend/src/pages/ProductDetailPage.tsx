import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Package,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Calendar
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
  ProductItem,
  ProductPerformancePoint
} from '../services/api';

export const ProductDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const productId = Number(id);

  const [product, setProduct] = useState<ProductItem | null>(null);
  const [performance, setPerformance] = useState<ProductPerformancePoint[]>([]);
  const [range, setRange] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!productId) return;
    fetchProductDetails();
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

  if (loading) {
    aria: 'Loading product details...';
  }

  if (error || !product) {
    return (
      <div className="p-8 text-center space-y-4">
        <div className="text-rose-400 font-medium text-sm">{error || 'Product not found.'}</div>
        <button
          onClick={() => navigate('/products')}
          className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-xs font-semibold hover:bg-slate-700"
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
    <div className="space-y-6 pb-12">
      
      {/* Back Button & Header */}
      <div>
        <button
          onClick={() => navigate('/products')}
          className="flex items-center gap-2 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-colors mb-3"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Products Catalog
        </button>

        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-950/60 px-2.5 py-1 rounded-lg border border-cyan-500/20">
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
            <p className="text-slate-400 text-xs mt-1.5">
              Category: <span className="text-slate-200 font-medium">{product.category || 'General'}</span> | Unit: <span className="text-slate-200 font-medium">{product.unit}</span>
            </p>
          </div>

          <div className="flex items-center gap-6">
            <div>
              <span className="text-[10px] font-semibold text-slate-400 block">Selling Price</span>
              <span className="text-lg font-bold text-emerald-400">₹{Number(product.selling_price).toFixed(2)}</span>
            </div>
            <div>
              <span className="text-[10px] font-semibold text-slate-400 block">Cost Price</span>
              <span className="text-lg font-bold text-slate-300">₹{Number(product.cost_price).toFixed(2)}</span>
            </div>
            <div>
              <span className="text-[10px] font-semibold text-slate-400 block">Min Stock Threshold</span>
              <span className="text-lg font-bold text-cyan-400">{product.min_stock_level} {product.unit}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Range Preset Selector */}
      <div className="flex items-center justify-between bg-slate-900/60 border border-slate-800 rounded-xl p-3 backdrop-blur-sm">
        <span className="text-xs font-semibold text-slate-400 flex items-center gap-1">
          <Calendar className="w-3.5 h-3.5 text-cyan-400" /> Performance Timeframe:
        </span>
        <div className="flex items-center gap-1.5">
          {['7d', '30d', '90d', '1y', 'all'].map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                range === r
                  ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {r.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-lg backdrop-blur-sm">
          <span className="text-[11px] font-semibold text-slate-400">Observed Units Sold</span>
          <div className="text-2xl font-bold text-slate-100 mt-2">{totalUnits.toLocaleString()} pcs</div>
          <span className="text-[10px] text-slate-500 mt-1 block">In selected timeframe</span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-lg backdrop-blur-sm">
          <span className="text-[11px] font-semibold text-slate-400">Confirmed Stockout Days</span>
          <div className="text-2xl font-bold text-rose-400 mt-2">{confirmedStockoutDays} days</div>
          <span className="text-[10px] text-slate-500 mt-1 block">is_stockout = TRUE</span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-lg backdrop-blur-sm">
          <span className="text-[11px] font-semibold text-slate-400">Zero EOD Inventory Days</span>
          <div className="text-2xl font-bold text-amber-400 mt-2">{zeroStockDays} days</div>
          <span className="text-[10px] text-slate-500 mt-1 block">stock_available = 0</span>
        </div>
      </div>

      {/* Composed Performance Timeline Chart */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-slate-200">Daily Observed Sales & Inventory Trajectory</h3>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5 text-cyan-400 font-medium">
              <span className="w-3 h-3 bg-cyan-500 rounded-sm inline-block" /> Observed Units Sold
            </span>
            <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <span className="w-3 h-0.5 bg-emerald-400 inline-block" /> End-of-Day Stock
            </span>
          </div>
        </div>

        <div className="h-80 w-full">
          {performance.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={performance} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                <XAxis dataKey="sale_date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" stroke="#06b6d4" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" stroke="#10b981" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                />
                <Bar yAxisId="left" dataKey="units_sold" name="Observed Units Sold" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                <Line yAxisId="right" type="monotone" dataKey="stock_available" name="Ending Inventory" stroke="#10b981" strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-xs">
              No historical records for this product in timeframe.
            </div>
          )}
        </div>
      </div>

    </div>
  );
};
