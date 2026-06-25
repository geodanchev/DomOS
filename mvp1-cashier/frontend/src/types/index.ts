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

export interface ApartmentCreate {
  number: string;
  floor?: number | null;
  owner_name: string;
  residents_count: number;
  monthly_fee: number;
  notes?: string | null;
}

export interface ApartmentUpdate {
  number?: string;
  floor?: number | null;
  owner_name?: string;
  residents_count?: number;
  monthly_fee?: number;
  notes?: string | null;
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
  receipt_id?: number | null;  // Auto-created receipt ID
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

// =============================================================================
// Obligation types (унифициран модел за задължения)
// Account-based система: Obligation съдържа само amount (без amount_paid, status)
// =============================================================================

export type ObligationType = 'monthly' | 'initial' | 'penalty' | 'repair' | 'fund' | 'other';

export interface Obligation {
  id: number;
  type: ObligationType;
  apartment_id: number;
  month: string | null;  // Само за monthly тип
  amount: number;        // Сума на задължението
  description: string | null;
  created_at: string;
  updated_at: string | null;
  // Допълнителни полета от API
  apartment_number?: string;
  owner_name?: string;
}

export interface ObligationCreate {
  type: ObligationType;
  apartment_id: number;
  month?: string | null;
  amount: number;
  description?: string | null;
}

export interface ObligationUpdate {
  amount?: number;
  description?: string | null;
}

export interface ObligationList {
  items: Obligation[];
  total: number;
}

export interface ObligationSummary {
  total_obligations: number;
  total_payments: number;
  balance: number;  // положителен = кредит, отрицателен = дължи
  count_obligations: number;
}

export interface MonthlyObligationsSummary extends ObligationSummary {
  month: string;
}

export interface ApartmentBalance {
  apartment_id: number;
  balance: number;  // positive = credit/overpaid, negative = owes
}

// =============================================================================
// Dashboard types (Account-based система)
// =============================================================================

export interface ApartmentStatus {
  apartment_id: number;
  apartment_number: string;
  owner_name: string;
  balance: number;           // Баланс на сметката (отрицателен = дължи)
  total_obligations: number; // Общо задължения
  total_payments: number;    // Общо плащания
  status: 'paid' | 'owes' | 'credit';  // Статус
  status_display: string;    // "Изплатен", "Дължи X лв", "Авансово X лв"
}

export interface CashierDashboard {
  total_apartments: number;
  total_collected: number;
  total_owed: number;        // Общо дължимо (сума на отрицателните баланси)
  collection_rate: number;
  paid_count: number;        // Брой изплатени (баланс >= 0)
  owes_count: number;        // Брой дължащи (баланс < 0)
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
  balance: number;           // Баланс (положителен = кредит, отрицателен = дължи)
  total_obligations: number; // Общо задължения
  total_payments: number;    // Общо плащания
}

// Receipt types
export interface ReceiptData {
  receipt_number: string;
  payment_id: number;
  payment_date: string;
  amount: number;
  payment_method: string;
  apartment_number: string;
  owner_name: string;
  month: string;
  collected_by: string;
  notes?: string | null;
}
