// User types
export interface User {
  id: number;
  username: string;
  display_name: string;
  role: 'admin' | 'cashier' | 'viewer';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Apartment types
export interface Apartment {
  id: number;
  number: string;
  floor: number | null;
  owner_name: string;
  residents_count: number;
  monthly_fee: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApartmentList {
  items: Apartment[];
  total: number;
}

// Payment types
export interface Payment {
  id: number;
  apartment_id: number;
  amount: number;
  month: string;
  payment_date: string;
  payment_method: string;
  collected_by_id: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  apartment_number?: string;
  owner_name?: string;
  collected_by_name?: string;
}

export interface PaymentCreate {
  apartment_id: number;
  amount: number;
  month: string;
  payment_method?: string;
  payment_date?: string;
  notes?: string;
}

export interface PaymentList {
  items: Payment[];
  total: number;
}

// Monthly charge types
export type ChargeStatus = 'paid' | 'partial' | 'unpaid';

export interface MonthlyCharge {
  id: number;
  apartment_id: number;
  month: string;
  amount_due: number;
  amount_paid: number;
  status: ChargeStatus;
  created_at: string;
  updated_at: string;
  apartment_number?: string;
  owner_name?: string;
}

export interface MonthlyChargeList {
  items: MonthlyCharge[];
  total: number;
}

// Dashboard types
export interface ApartmentStatus {
  apartment_id: number;
  apartment_number: string;
  owner_name: string;
  amount_due: number;
  amount_paid: number;
  status: ChargeStatus;
  status_display: string;
}

export interface CashierDashboard {
  total_apartments: number;
  total_collected: number;
  total_unpaid: number;
  collection_rate: number;
  paid_count: number;
  partial_count: number;
  unpaid_count: number;
  current_month: string;
  apartments: ApartmentStatus[];
}

export interface FundBalance {
  total_collected_all_time: number;
  total_expenses: number;
  current_balance: number;
}

// Payment summary types for payment dialog
export interface RecentPayment {
  id: number;
  amount: number;
  month: string;
  payment_date: string;
  payment_method: string;
}

export interface ApartmentPaymentSummary {
  apartment_id: number;
  apartment_number: string;
  owner_name: string;
  recent_payments: RecentPayment[];
  current_balance: number;  // positive = owes, negative = overpaid
  total_due: number;
  total_paid: number;
}
