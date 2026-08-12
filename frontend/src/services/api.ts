import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach Bearer token if present
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('retailmind_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: handle 401 unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('retailmind_token');
    }
    return Promise.reject(error);
  }
);

// Analytics API
export interface AnalyticsSummary {
  total_revenue: string;
  observed_units_sold: number;
  avg_revenue_per_recorded_day: string;
  active_catalog_size: number;
  confirmed_stockout_days: number;
  zero_eod_stock_days: number;
  start_date?: string;
  end_date?: string;
}

export interface CSVImportResult {
  success: boolean;
  total_rows_processed: number;
  successful_imports: number;
  errors: Array<{ row_number: number; column?: string; error: string }>;
  message: string;
}

export interface SalesTrendPoint {
  sale_date: string;
  revenue: string;
  units_sold: number;
  promo_active: boolean;
}

export interface CategoryBreakdown {
  category: string;
  revenue: string;
  units_sold: number;
  percentage_share: number;
}

export interface TopProductItem {
  product_id: number;
  sku: string;
  name: string;
  category: string | null;
  total_revenue: string;
  total_units_sold: number;
}

export interface ProductPerformancePoint {
  sale_date: string;
  units_sold: number;
  selling_price: string;
  stock_available: number;
  is_stockout: boolean | null;
}

export interface DataQualityReport {
  quality_score: number;
  total_recorded_days: number;
  expected_days: number;
  date_coverage_ratio: number;
  date_gaps_count: number;
  anomalies_count: number;
  stockout_censored_ratio: number;
  status: string;
}

export interface ProductItem {
  id: number;
  business_id: number;
  sku: string;
  name: string;
  category: string | null;
  unit: string;
  cost_price: string;
  selling_price: string;
  min_stock_level: number;
  is_active: boolean;
  created_at: string;
}

export const analyticsApi = {
  getSummary: (params?: { range?: string; start_date?: string; end_date?: string; category?: string }) =>
    api.get<AnalyticsSummary>('/api/v1/analytics/summary', { params }),

  getSalesTrend: (params?: { range?: string; start_date?: string; end_date?: string; category?: string }) =>
    api.get<SalesTrendPoint[]>('/api/v1/analytics/sales-trend', { params }),

  getCategoryBreakdown: (params?: { range?: string; start_date?: string; end_date?: string }) =>
    api.get<CategoryBreakdown[]>('/api/v1/analytics/category-breakdown', { params }),

  getTopProducts: (params?: { limit?: number; range?: string; start_date?: string; end_date?: string }) =>
    api.get<TopProductItem[]>('/api/v1/analytics/top-products', { params }),

  getProductPerformance: (productId: number, params?: { range?: string; start_date?: string; end_date?: string }) =>
    api.get<ProductPerformancePoint[]>(`/api/v1/analytics/product-performance/${productId}`, { params }),

  getDataQuality: (params?: { range?: string; start_date?: string; end_date?: string }) =>
    api.get<DataQualityReport>('/api/v1/analytics/data-quality', { params }),
};

export const productsApi = {
  listProducts: (params?: { include_inactive?: boolean; category?: string; search?: string; limit?: number; offset?: number }) =>
    api.get<ProductItem[]>('/api/v1/products', { params }),

  getProduct: (id: number) =>
    api.get<ProductItem>(`/api/v1/products/${id}`),

  createProduct: (data: { sku: string; name: string; category?: string; unit?: string; cost_price?: number; selling_price?: number; min_stock_level?: number }) =>
    api.post<ProductItem>('/api/v1/products', data),

  updateProduct: (id: number, data: Partial<ProductItem>) =>
    api.put<ProductItem>(`/api/v1/products/${id}`, data),

  deactivateProduct: (id: number) =>
    api.delete<{ success: boolean; product_id: number; is_active: boolean; message: string }>(`/api/v1/products/${id}`),
};
