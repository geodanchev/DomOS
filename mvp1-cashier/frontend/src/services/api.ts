import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  LoginResponse,
  User,
  ApartmentList,
  Apartment,
  PaymentList,
  Payment,
  PaymentCreate,
  MonthlyChargeList,
  CashierDashboard,
  FundBalance,
  ApartmentPaymentSummary,
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

// Monthly Charges API
export const chargesApi = {
  getAll: async (month?: string): Promise<MonthlyChargeList> => {
    const params = month ? `?month=${month}` : '';
    const response = await api.get<MonthlyChargeList>(`/charges${params}`);
    return response.data;
  },
  
  generate: async (month: string): Promise<{ message: string; count: number }> => {
    const response = await api.post<{ message: string; count: number }>(
      `/charges/generate?month=${month}`
    );
    return response.data;
  },
};

// Dashboard API
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
