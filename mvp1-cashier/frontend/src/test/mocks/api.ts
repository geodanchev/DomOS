import { vi } from 'vitest'
import { mockLoginResponse, mockApartments, mockPayments, mockDashboard, mockFundBalance } from './data'

// Mock the api module
export const mockAuthApi = {
  login: vi.fn().mockResolvedValue(mockLoginResponse),
  getMe: vi.fn().mockResolvedValue(mockLoginResponse.user),
}

export const mockApartmentsApi = {
  getAll: vi.fn().mockResolvedValue({ items: mockApartments, total: mockApartments.length }),
  getById: vi.fn().mockImplementation((id: number) => {
    const apt = mockApartments.find(a => a.id === id)
    return Promise.resolve(apt)
  }),
}

export const mockPaymentsApi = {
  getAll: vi.fn().mockResolvedValue({ items: mockPayments, total: mockPayments.length }),
  create: vi.fn().mockImplementation((data) => {
    const newPayment = {
      id: 999,
      ...data,
      collected_by_id: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      apartment_number: '1',
      owner_name: 'Test Owner',
      collected_by_name: 'Administrator',
    }
    return Promise.resolve(newPayment)
  }),
  getById: vi.fn().mockImplementation((id: number) => {
    const payment = mockPayments.find(p => p.id === id)
    return Promise.resolve(payment)
  }),
  delete: vi.fn().mockResolvedValue(undefined),
}

export const mockChargesApi = {
  getAll: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  generate: vi.fn().mockResolvedValue({ message: 'Generated', count: 3 }),
}

export const mockDashboardApi = {
  getDashboard: vi.fn().mockResolvedValue(mockDashboard),
  getFundBalance: vi.fn().mockResolvedValue(mockFundBalance),
}

// Function to reset all mocks
export const resetAllMocks = () => {
  mockAuthApi.login.mockClear()
  mockAuthApi.getMe.mockClear()
  mockApartmentsApi.getAll.mockClear()
  mockApartmentsApi.getById.mockClear()
  mockPaymentsApi.getAll.mockClear()
  mockPaymentsApi.create.mockClear()
  mockPaymentsApi.getById.mockClear()
  mockPaymentsApi.delete.mockClear()
  mockChargesApi.getAll.mockClear()
  mockChargesApi.generate.mockClear()
  mockDashboardApi.getDashboard.mockClear()
  mockDashboardApi.getFundBalance.mockClear()
}
