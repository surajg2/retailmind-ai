import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Package, UploadCloud, LogOut, Store } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Analytics', icon: LayoutDashboard },
    { path: '/products', label: 'Products', icon: Package },
    { path: '/import', label: 'Import Data', icon: UploadCloud },
  ];

  return (
    <nav className="bg-zinc-950/90 backdrop-blur-md border-b border-zinc-800/80 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-zinc-900 border border-zinc-700/80 flex items-center justify-center shadow-md">
              <Store className="w-5 h-5 text-zinc-100" />
            </div>
            <div>
              <span className="text-base font-bold bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
                RetailMind AI
              </span>
              <span className="hidden sm:inline-block ml-2 text-[10px] font-bold text-zinc-300 bg-zinc-900 px-2 py-0.5 rounded-full border border-zinc-700/80 tracking-wider">
                INTELLIGENCE
              </span>
            </div>
          </div>

          {/* Navigation Rail with Accent Indicator Line */}
          <div className="flex items-center space-x-1 sm:space-x-4">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
              
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`nav-rail-item relative flex items-center gap-2 px-3 py-4 text-xs font-semibold transition-colors ${
                    isActive ? 'text-zinc-100 font-bold' : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                  {isActive && <div className="nav-rail-indicator" />}
                </NavLink>
              );
            })}
          </div>

          {/* User Profile & Logout */}
          <div className="flex items-center gap-3">
            {user?.business && (
              <div className="hidden md:flex flex-col text-right">
                <span className="text-xs font-bold text-zinc-200">{user.business.name}</span>
                <span className="text-[10px] text-zinc-400 font-mono">{user.email}</span>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="tactile-button p-2 text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl border border-transparent hover:border-rose-500/20 transition-all"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>

        </div>
      </div>
    </nav>
  );
};
