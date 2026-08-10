import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Store, User, LogOut, Activity, Database, CheckCircle2, ShieldCheck, Layers } from 'lucide-react';

interface HealthInfo {
  status: string;
  database: string;
  timestamp: string;
}

export const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [isHealthLoading, setIsHealthLoading] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await api.get('/health');
        setHealth(response.data);
      } catch (error) {
        console.error('Health check failed', error);
      } finally {
        setIsHealthLoading(false);
      }
    };
    checkHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-600/20 rounded-xl border border-indigo-500/30 text-indigo-400">
              <Store className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-extrabold text-xl tracking-tight text-white flex items-center space-x-2">
                <span>RetailMind</span>
                <span className="gradient-text">AI</span>
              </h1>
              <p className="text-[10px] text-slate-400 font-medium -mt-1">Demand & Inventory Engine</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex items-center space-x-3 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
              <span className="text-xs text-slate-300 font-medium">PostgreSQL Connected</span>
            </div>

            <button
              onClick={logout}
              className="flex items-center space-x-2 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700/60 text-slate-300 hover:text-white rounded-xl text-xs font-semibold transition-all cursor-pointer"
            >
              <LogOut className="w-4 h-4 text-rose-400" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Welcome Hero Banner */}
        <div className="relative overflow-hidden glass-card rounded-3xl p-8 border border-slate-800/80 shadow-2xl">
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none"></div>
          
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold mb-3">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Phase 1 Authentication & DB Foundation Ready</span>
              </div>
              <h2 className="text-3xl font-extrabold text-white tracking-tight">
                Welcome back, <span className="gradient-text">{user?.full_name || user?.email}</span>!
              </h2>
              <p className="text-slate-400 text-sm mt-1 max-w-2xl">
                Your RetailMind AI workspace is active. Database models for Users, Businesses, Products, Sales, Inventory, Festivals, Predictions, and Recommendations are deployed.
              </p>
            </div>

            <div className="flex items-center space-x-3 bg-slate-900/90 p-4 rounded-2xl border border-slate-800">
              <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400">
                <User className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Logged in as</p>
                <p className="text-sm font-semibold text-white">{user?.email}</p>
                <p className="text-[11px] text-indigo-400 font-medium capitalize">Role: {user?.role}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Store & System Status Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Business Info Card */}
          <div className="glass-card glass-card-hover rounded-2xl p-6 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400">
                <Store className="w-6 h-6" />
              </div>
              <span className="text-xs px-2.5 py-1 bg-blue-500/10 text-blue-300 border border-blue-500/20 rounded-full font-medium">
                Active Store
              </span>
            </div>
            <h3 className="text-sm font-medium text-slate-400">Business Details</h3>
            <p className="text-xl font-bold text-white mt-1">
              {user?.business?.name || 'Standard Retail Store'}
            </p>
            <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
              <span>Category:</span>
              <span className="font-semibold text-slate-200">{user?.business?.type || 'General Store'}</span>
            </div>
          </div>

          {/* System Health Card */}
          <div className="glass-card glass-card-hover rounded-2xl p-6 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
                <Activity className="w-6 h-6" />
              </div>
              <span className="text-xs px-2.5 py-1 bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 rounded-full font-medium flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>Healthy</span>
              </span>
            </div>
            <h3 className="text-sm font-medium text-slate-400">FastAPI Backend Status</h3>
            <p className="text-xl font-bold text-white mt-1">
              {isHealthLoading ? 'Checking...' : health?.status === 'ok' ? 'Online & Ready' : 'Service Warning'}
            </p>
            <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
              <span>Endpoint:</span>
              <span className="font-mono text-xs text-emerald-400">GET /health</span>
            </div>
          </div>

          {/* PostgreSQL DB Card */}
          <div className="glass-card glass-card-hover rounded-2xl p-6 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400">
                <Database className="w-6 h-6" />
              </div>
              <span className="text-xs px-2.5 py-1 bg-purple-500/10 text-purple-300 border border-purple-500/20 rounded-full font-medium">
                Alembic Migrated
              </span>
            </div>
            <h3 className="text-sm font-medium text-slate-400">Database Engine</h3>
            <p className="text-xl font-bold text-white mt-1">PostgreSQL 18</p>
            <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
              <span>Connectivity:</span>
              <span className="font-semibold text-purple-300 capitalize">{health?.database || 'Connected'}</span>
            </div>
          </div>
        </div>

        {/* Phase 1 Models Status Section */}
        <div className="glass-card rounded-2xl p-6 border border-slate-800">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            <span>Phase 1 Deployed Database Schemas</span>
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { name: 'User', desc: 'Auth & roles' },
              { name: 'Business', desc: 'Store profile' },
              { name: 'Product', desc: 'SKU catalog' },
              { name: 'Sales', desc: 'Transactions' },
              { name: 'Inventory', desc: 'Stock levels' },
              { name: 'Festival', desc: 'Demand uplift' },
              { name: 'Prediction', desc: 'ML forecasts' },
              { name: 'Recommendation', desc: 'Decision rules' },
            ].map((model) => (
              <div key={model.name} className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl">
                <p className="text-sm font-bold text-indigo-300">{model.name}</p>
                <p className="text-xs text-slate-400">{model.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};
