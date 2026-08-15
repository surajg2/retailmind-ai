import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Store, Lock, Mail, User as UserIcon, Building, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [businessName, setBusinessName] = useState('');
  const [businessType, setBusinessType] = useState('Kirana / General Store');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  
  const { register, error: authError, clearError } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    clearError();

    if (!email || !password || !fullName || !businessName) {
      setFormError('Please fill in all required fields.');
      return;
    }

    if (password.length < 6) {
      setFormError('Password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setFormError('Passwords do not match.');
      return;
    }

    try {
      setIsSubmitting(true);
      await register({
        email,
        password,
        full_name: fullName,
        business_name: businessName,
        business_type: businessType,
      });
      navigate('/');
    } catch (err: any) {
      setFormError(err.message || 'Registration failed. Please check your inputs.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-data-wipe min-h-screen bg-zinc-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="flex justify-center items-center space-x-3 mb-2">
          <div className="p-3 bg-zinc-900 rounded-2xl border border-zinc-800 text-zinc-100 shadow-md">
            <Store className="w-8 h-8 text-zinc-100" />
          </div>
        </div>
        <h2 className="text-center text-3xl font-extrabold tracking-tight text-white">
          RetailMind AI
        </h2>
        <p className="mt-2 text-center text-xs text-zinc-400">
          Create your retail business account
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4">
        <div className="bg-zinc-900/90 rounded-2xl p-8 shadow-2xl border border-zinc-800 backdrop-blur-md">
          <div className="mb-6">
            <h3 className="text-xl font-bold text-white mb-1">Get Started</h3>
            <p className="text-xs text-zinc-400">Set up your business and start managing store sales</p>
          </div>

          {(formError || authError) && (
            <div className="mb-6 bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="text-xs text-rose-300">
                {formError || authError}
              </div>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5">
                Full Name
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
                  <UserIcon className="h-4 w-4" />
                </div>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Suraj Gupta"
                  className="block w-full pl-10 pr-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500 text-sm transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5">
                Business / Store Name
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
                  <Building className="h-4 w-4" />
                </div>
                <input
                  type="text"
                  required
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  placeholder="Suraj Kirana & Superstore"
                  className="block w-full pl-10 pr-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500 text-sm transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5">
                Business Type
              </label>
              <select
                value={businessType}
                onChange={(e) => setBusinessType(e.target.value)}
                className="block w-full px-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-100 focus:outline-none focus:border-zinc-500 text-sm transition-all"
              >
                <option value="Kirana / General Store">Kirana / General Store</option>
                <option value="Supermarket / Groceries">Supermarket / Groceries</option>
                <option value="FMCG & Provisions">FMCG & Provisions</option>
                <option value="Apparel & Garments">Apparel & Garments</option>
                <option value="Electronics & Accessories">Electronics & Accessories</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="suraj@kirana.com"
                  className="block w-full pl-10 pr-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500 text-sm transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  className="block w-full pl-10 pr-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500 text-sm transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5">
                Confirm Password
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
                  className="block w-full pl-10 pr-4 py-2.5 bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500 text-sm transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="tactile-button w-full flex justify-center items-center py-3.5 px-4 rounded-xl text-sm font-bold text-zinc-950 bg-zinc-100 hover:bg-white focus:outline-none shadow-md disabled:opacity-50 transition-all cursor-pointer mt-6"
            >
              {isSubmitting ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-zinc-950/30 border-t-zinc-950 rounded-full animate-spin"></div>
                  <span>Creating Account...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <span>Register & Launch Dashboard</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-zinc-800/80 text-center">
            <p className="text-xs text-zinc-400">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-zinc-200 hover:text-white transition-colors">
                Sign In
              </Link>
            </p>
          </div>
        </div>

        <div className="mt-6 text-center flex items-center justify-center space-x-2 text-xs text-zinc-500">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>PostgreSQL DB Initialized & Alembic Migrations Active</span>
        </div>
      </div>
    </div>
  );
};
