import type { User, Apartment, Payment, MonthlyCharge, CashierDashboard, FundBalance, LoginResponse } from '../../types'

export const mockUser: User = {
  id: 1,
  username: 'admin',
  display_name: 'Administrator',
  role: 'admin',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

export const mockCashierUser: User = {
  id: 2,
  username: 'cashier',
  display_name: 'Касиер',
  role: 'cashier',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

export const mockLoginResponse: LoginResponse = {
  access_token: 'mock-jwt-token',
  token_type: 'bearer',
  user: mockUser,
}

export const mockApartments: Apartment[] = [
  {
    id: 1,
    number: '1',
    floor: 1,
    owner_name: 'Иван Петров',
    residents_count: 3,
    monthly_fee: 50,
    notes: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    number: '2',
    floor: 1,
    owner_name: 'Мария Иванова',
    residents_count: 2,
    monthly_fee: 45,
    notes: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 3,
    number: '3',
    floor: 2,
    owner_name: 'Георги Димитров',
    residents_count: 4,
    monthly_fee: 55,
    notes: 'VIP',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

export const mockPayments: Payment[] = [
  {
    id: 1,
    apartment_id: 1,
    amount: 50,
    month: '2024-01',
    payment_date: '2024-01-15',
    payment_method: 'cash',
    collected_by_id: 1,
    notes: null,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    apartment_number: '1',
    owner_name: 'Иван Петров',
    collected_by_name: 'Administrator',
  },
  {
    id: 2,
    apartment_id: 2,
    amount: 20,
    month: '2024-01',
    payment_date: '2024-01-20',
    payment_method: 'card',
    collected_by_id: 1,
    notes: 'Частично плащане',
    created_at: '2024-01-20T14:00:00Z',
    updated_at: '2024-01-20T14:00:00Z',
    apartment_number: '2',
    owner_name: 'Мария Иванова',
    collected_by_name: 'Administrator',
  },
]

export const mockMonthlyCharges: MonthlyCharge[] = [
  {
    id: 1,
    apartment_id: 1,
    month: '2024-01',
    amount_due: 50,
    amount_paid: 50,
    status: 'paid',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    apartment_number: '1',
    owner_name: 'Иван Петров',
  },
  {
    id: 2,
    apartment_id: 2,
    month: '2024-01',
    amount_due: 45,
    amount_paid: 20,
    status: 'partial',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-20T14:00:00Z',
    apartment_number: '2',
    owner_name: 'Мария Иванова',
  },
  {
    id: 3,
    apartment_id: 3,
    month: '2024-01',
    amount_due: 55,
    amount_paid: 0,
    status: 'unpaid',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    apartment_number: '3',
    owner_name: 'Георги Димитров',
  },
]

export const mockDashboard: CashierDashboard = {
  total_apartments: 3,
  total_collected: 70,
  total_unpaid: 80,
  collection_rate: 46.67,
  paid_count: 1,
  partial_count: 1,
  unpaid_count: 1,
  current_month: '2024-01',
  apartments: [
    {
      apartment_id: 1,
      apartment_number: '1',
      owner_name: 'Иван Петров',
      amount_due: 50,
      amount_paid: 50,
      status: 'paid',
      status_display: 'Платено',
    },
    {
      apartment_id: 2,
      apartment_number: '2',
      owner_name: 'Мария Иванова',
      amount_due: 45,
      amount_paid: 20,
      status: 'partial',
      status_display: 'Частично',
    },
    {
      apartment_id: 3,
      apartment_number: '3',
      owner_name: 'Георги Димитров',
      amount_due: 55,
      amount_paid: 0,
      status: 'unpaid',
      status_display: 'Неплатено',
    },
  ],
}

export const mockFundBalance: FundBalance = {
  total_collected_all_time: 1500,
  total_expenses: 200,
  current_balance: 1300,
}
