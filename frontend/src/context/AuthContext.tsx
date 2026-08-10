import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

export interface Business {
  id: number;
  name: string;
  type?: string;
  location?: string;
}

export interface User {
  id: number;
  email: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  business_id?: number;
  business?: Business;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; full_name?: string; business_name?: string; business_type?: string }) => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('retailmind_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCurrentUser = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/api/v1/auth/me');
      setUser(response.data);
    } catch (err: any) {
      console.error('Failed to load user session', err);
      setUser(null);
      setToken(null);
      localStorage.removeItem('retailmind_token');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const response = await api.post('/api/v1/auth/login', { email, password });
      const accessToken = response.data.access_token;
      localStorage.setItem('retailmind_token', accessToken);
      setToken(accessToken);
      const userResp = await api.get('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${accessToken}` }
      });
      setUser(userResp.data);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Login failed. Please check your credentials.';
      setError(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: { email: string; password: string; full_name?: string; business_name?: string; business_type?: string }) => {
    setError(null);
    setIsLoading(true);
    try {
      await api.post('/api/v1/auth/register', data);
      // Auto login after registration
      await login(data.email, data.password);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed. Please try again.';
      setError(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('retailmind_token');
    setToken(null);
    setUser(null);
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        error,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
