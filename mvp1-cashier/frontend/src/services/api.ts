import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  LoginResponse,
  User,
  ApartmentList,
  Apartment,
  ApartmentCreate,
  ApartmentUpdate,
  PaymentList,
  Payment,
  PaymentCreate,
  CashierDashboard,
  FundBalance,
  ApartmentPaymentSummary,
  // Obligation types
  Obligation,
  ObligationCreate,
  ObligationUpdate,
  ObligationType,
  ObligationSummary,
  MonthlyObligationsSummary,
  ApartmentBalance,
} from '../types';

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post<LoginResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },
  
  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};

// Apartments API
export const apartmentsApi = {
  getAll: async (): Promise<ApartmentList> => {
    const response = await api.get<ApartmentList>('/apartments');
    return response.data;
  },
  
  getById: async (id: number): Promise<Apartment> => {
    const response = await api.get<Apartment>(`/apartments/${id}`);
    return response.data;
  },
  
  create: async (data: ApartmentCreate): Promise<Apartment> => {
    const response = await api.post<Apartment>('/apartments', data);
    return response.data;
  },
  
  update: async (id: number, data: ApartmentUpdate): Promise<Apartment> => {
    const response = await api.put<Apartment>(`/apartments/${id}`, data);
    return response.data;
  },
  
  delete: async (id: number): Promise<void> => {
    await api.delete(`/apartments/${id}`);
  },
};

// Payments API
export const paymentsApi = {
  getAll: async (apartmentId?: number, month?: string): Promise<PaymentList> => {
    const params = new URLSearchParams();
    if (apartmentId) params.append('apartment_id', apartmentId.toString());
    if (month) params.append('month', month);
    
    const response = await api.get<PaymentList>(`/payments?${params}`);
    return response.data;
  },
  
  create: async (data: PaymentCreate): Promise<Payment> => {
    const response = await api.post<Payment>('/payments', data);
    return response.data;
  },
  
  getById: async (id: number): Promise<Payment> => {
    const response = await api.get<Payment>(`/payments/${id}`);
    return response.data;
  },
  
  delete: async (id: number): Promise<void> => {
    await api.delete(`/payments/${id}`);
  },
  
  getApartmentSummary: async (apartmentId: number): Promise<ApartmentPaymentSummary> => {
    const response = await api.get<ApartmentPaymentSummary>(`/payments/apartment/${apartmentId}/summary`);
    return response.data;
  },
};

// =============================================================================
// Obligations API (унифициран модел за задължения)
// =============================================================================

export interface ObligationFilters {
  skip?: number;
  limit?: number;
  type?: ObligationType;
  apartment_id?: number;
  month?: string;
}

export const obligationsApi = {
  // CRUD операции
  getAll: async (filters?: ObligationFilters): Promise<Obligation[]> => {
    const params = new URLSearchParams();
    if (filters?.skip) params.append('skip', filters.skip.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.type) params.append('type', filters.type);
    if (filters?.apartment_id) params.append('apartment_id', filters.apartment_id.toString());
    if (filters?.month) params.append('month', filters.month);
    
    const response = await api.get<Obligation[]>(`/obligations?${params}`);
    return response.data;
  },
  
  getById: async (id: number): Promise<Obligation> => {
    const response = await api.get<Obligation>(`/obligations/${id}`);
    return response.data;
  },
  
  create: async (data: ObligationCreate): Promise<Obligation> => {
    const response = await api.post<Obligation>('/obligations/', data);
    return response.data;
  },
  
  update: async (id: number, data: ObligationUpdate): Promise<Obligation> => {
    const response = await api.patch<Obligation>(`/obligations/${id}`, data);
    return response.data;
  },
  
  delete: async (id: number): Promise<void> => {
    await api.delete(`/obligations/${id}`);
  },
  
  // Apartment-specific
  getByApartment: async (apartmentId: number): Promise<Obligation[]> => {
    const response = await api.get<Obligation[]>(`/obligations/apartment/${apartmentId}`);
    return response.data;
  },
  
  getApartmentBalance: async (apartmentId: number): Promise<ApartmentBalance> => {
    const response = await api.get<ApartmentBalance>(`/obligations/apartment/${apartmentId}/balance`);
    return response.data;
  },
  
  // Monthly generation
  generateMonthly: async (month: string): Promise<Obligation[]> => {
    const response = await api.post<Obligation[]>(`/obligations/generate-monthly?month=${month}`);
    return response.data;
  },
  
  // Statistics
  getSummary: async (filters?: { apartment_id?: number; month?: string; type?: ObligationType }): Promise<ObligationSummary> => {
    const params = new URLSearchParams();
    if (filters?.apartment_id) params.append('apartment_id', filters.apartment_id.toString());
    if (filters?.month) params.append('month', filters.month);
    if (filters?.type) params.append('type', filters.type);
    
    const response = await api.get<ObligationSummary>(`/obligations/stats/summary?${params}`);
    return response.data;
  },
  
  getMonthlySummary: async (month: string): Promise<MonthlyObligationsSummary> => {
    const response = await api.get<MonthlyObligationsSummary>(`/obligations/stats/monthly/${month}`);
    return response.data;
  },
};

// =============================================================================
// Dashboard API
// =============================================================================

export const dashboardApi = {
  getDashboard: async (month?: string): Promise<CashierDashboard> => {
    const params = month ? `?month=${month}` : '';
    const response = await api.get<CashierDashboard>(`/dashboard${params}`);
    return response.data;
  },
  
  getFundBalance: async (): Promise<FundBalance> => {
    const response = await api.get<FundBalance>('/dashboard/fund');
    return response.data;
  },
};

export default api;
