import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Use vi.hoisted to create mock functions that are available during hoisting
const { mockGet, mockPost, mockPut, mockPatch, mockDelete } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockPatch: vi.fn(),
  mockDelete: vi.fn(),
}));

// Mock axios with factory function
vi.mock('axios', () => {
  return {
    default: {
      create: vi.fn(() => ({
        get: mockGet,
        post: mockPost,
        put: mockPut,
        patch: mockPatch,
        delete: mockDelete,
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      })),
    },
  };
});

// Import after mocking
import {
  authApi,
  apartmentsApi,
  paymentsApi,
  obligationsApi,
  dashboardApi,
  receiptsApi,
} from './api';

describe('API Services', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // =========================================================================
  // Auth API Tests
  // =========================================================================
  describe('authApi', () => {
    describe('login', () => {
      it('should send login request with form data', async () => {
        const mockResponse = {
          data: {
            access_token: 'test-token',
            token_type: 'bearer',
            user: { id: 1, username: 'admin', role: 'admin' },
          },
        };
        mockPost.mockResolvedValueOnce(mockResponse);

        const result = await authApi.login('admin', 'password123');

        expect(mockPost).toHaveBeenCalledTimes(1);
        expect(mockPost).toHaveBeenCalledWith(
          '/auth/login',
          expect.any(URLSearchParams),
          { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
        );
        
        // Verify URLSearchParams content
        const calledFormData = mockPost.mock.calls[0][1] as URLSearchParams;
        expect(calledFormData.get('username')).toBe('admin');
        expect(calledFormData.get('password')).toBe('password123');
        
        expect(result).toEqual(mockResponse.data);
      });

      it('should throw error on invalid credentials', async () => {
        const error = {
          response: {
            status: 401,
            data: { detail: 'Incorrect username or password' },
          },
        };
        mockPost.mockRejectedValueOnce(error);

        await expect(authApi.login('wrong', 'wrong')).rejects.toEqual(error);
      });
    });

    describe('getMe', () => {
      it('should fetch current user', async () => {
        const mockUser = {
          data: {
            id: 1,
            username: 'admin',
            full_name: 'Administrator',
            role: 'admin',
          },
        };
        mockGet.mockResolvedValueOnce(mockUser);

        const result = await authApi.getMe();

        expect(mockGet).toHaveBeenCalledTimes(1);
        expect(mockGet).toHaveBeenCalledWith('/auth/me');
        expect(result).toEqual(mockUser.data);
      });

      it('should throw error on 401 unauthorized', async () => {
        const error = {
          response: {
            status: 401,
            data: { detail: 'Not authenticated' },
          },
        };
        mockGet.mockRejectedValueOnce(error);

        await expect(authApi.getMe()).rejects.toEqual(error);
      });
    });
  });

  // =========================================================================
  // Apartments API Tests
  // =========================================================================
  describe('apartmentsApi', () => {
    describe('getAll', () => {
      it('should fetch all apartments', async () => {
        const mockApartments = {
          data: {
            items: [
              { id: 1, number: '1', floor: 1, owner_name: 'Иван Иванов' },
              { id: 2, number: '2', floor: 1, owner_name: 'Петър Петров' },
            ],
            total: 2,
          },
        };
        mockGet.mockResolvedValueOnce(mockApartments);

        const result = await apartmentsApi.getAll();

        expect(mockGet).toHaveBeenCalledTimes(1);
        expect(mockGet).toHaveBeenCalledWith('/apartments');
        expect(result).toEqual(mockApartments.data);
      });

      it('should handle empty apartments list', async () => {
        const mockEmptyList = {
          data: {
            items: [],
            total: 0,
          },
        };
        mockGet.mockResolvedValueOnce(mockEmptyList);

        const result = await apartmentsApi.getAll();

        expect(result.items).toHaveLength(0);
        expect(result.total).toBe(0);
      });
    });

    describe('getById', () => {
      it('should fetch apartment by id', async () => {
        const mockApartment = {
          data: {
            id: 1,
            number: '1',
            floor: 1,
            owner_name: 'Иван Иванов',
            monthly_fee: 10.0,
          },
        };
        mockGet.mockResolvedValueOnce(mockApartment);

        const result = await apartmentsApi.getById(1);

        expect(mockGet).toHaveBeenCalledWith('/apartments/1');
        expect(result).toEqual(mockApartment.data);
      });

      it('should throw error for non-existent apartment', async () => {
        const error = {
          response: {
            status: 404,
            data: { detail: 'Apartment not found' },
          },
        };
        mockGet.mockRejectedValueOnce(error);

        await expect(apartmentsApi.getById(999)).rejects.toEqual(error);
      });
    });

    describe('create', () => {
      it('should create new apartment', async () => {
        const newApartment = {
          number: '10',
          floor: 3,
          owner_name: 'Нов Собственик',
          monthly_fee: 15.0,
        };
        const mockResponse = {
          data: { id: 10, ...newApartment },
        };
        mockPost.mockResolvedValueOnce(mockResponse);

        const result = await apartmentsApi.create(newApartment);

        expect(mockPost).toHaveBeenCalledWith('/apartments', newApartment);
        expect(result).toEqual(mockResponse.data);
      });
    });

    describe('update', () => {
      it('should update existing apartment', async () => {
        const updateData = { owner_name: 'Обновен Собственик' };
        const mockResponse = {
          data: {
            id: 1,
            number: '1',
            floor: 1,
            owner_name: 'Обновен Собственик',
          },
        };
        mockPut.mockResolvedValueOnce(mockResponse);

        const result = await apartmentsApi.update(1, updateData);

        expect(mockPut).toHaveBeenCalledWith('/apartments/1', updateData);
        expect(result).toEqual(mockResponse.data);
      });
    });

    describe('delete', () => {
      it('should delete apartment', async () => {
        mockDelete.mockResolvedValueOnce({ data: null });

        await apartmentsApi.delete(1);

        expect(mockDelete).toHaveBeenCalledWith('/apartments/1');
      });
    });
  });

  // =========================================================================
  // Payments API Tests
  // =========================================================================
  describe('paymentsApi', () => {
    describe('getAll', () => {
      it('should fetch all payments without filters', async () => {
        const mockPayments = {
          data: {
            items: [
              { id: 1, amount: 100, apartment_id: 1, month: '2026-01' },
            ],
            total: 1,
          },
        };
        mockGet.mockResolvedValueOnce(mockPayments);

        const result = await paymentsApi.getAll();

        expect(mockGet).toHaveBeenCalledWith('/payments?');
        expect(result).toEqual(mockPayments.data);
      });

      it('should fetch payments with apartment filter', async () => {
        const mockPayments = {
          data: {
            items: [
              { id: 1, amount: 100, apartment_id: 5, month: '2026-01' },
            ],
            total: 1,
          },
        };
        mockGet.mockResolvedValueOnce(mockPayments);

        const result = await paymentsApi.getAll(5);

        expect(mockGet).toHaveBeenCalledWith('/payments?apartment_id=5');
        expect(result).toEqual(mockPayments.data);
      });

      it('should fetch payments with apartment and month filters', async () => {
        const mockPayments = { data: { items: [], total: 0 } };
        mockGet.mockResolvedValueOnce(mockPayments);

        await paymentsApi.getAll(5, '2026-01');

        expect(mockGet).toHaveBeenCalledWith('/payments?apartment_id=5&month=2026-01');
      });
    });

    describe('create', () => {
      it('should create new payment', async () => {
        const paymentData = {
          apartment_id: 1,
          amount: 50.0,
          month: '2026-01',
          payment_method: 'cash' as const,
        };
        const mockResponse = {
          data: {
            id: 1,
            ...paymentData,
            payment_date: '2026-01-15T10:00:00',
            receipt_id: 123,
          },
        };
        mockPost.mockResolvedValueOnce(mockResponse);

        const result = await paymentsApi.create(paymentData);

        expect(mockPost).toHaveBeenCalledWith('/payments', paymentData);
        expect(result).toEqual(mockResponse.data);
        expect(result.receipt_id).toBe(123);
      });

      it('should handle validation error on create', async () => {
        const error = {
          response: {
            status: 422,
            data: { detail: 'Invalid amount' },
          },
        };
        mockPost.mockRejectedValueOnce(error);

        await expect(paymentsApi.create({ amount: -10 } as any)).rejects.toEqual(error);
      });
    });

    describe('getById', () => {
      it('should fetch payment by id', async () => {
        const mockPayment = {
          data: { id: 1, amount: 100, apartment_id: 1 },
        };
        mockGet.mockResolvedValueOnce(mockPayment);

        const result = await paymentsApi.getById(1);

        expect(mockGet).toHaveBeenCalledWith('/payments/1');
        expect(result).toEqual(mockPayment.data);
      });
    });

    describe('getApartmentSummary', () => {
      it('should fetch apartment payment summary', async () => {
        const mockSummary = {
          data: {
            apartment_id: 1,
            apartment_number: '1',
            owner_name: 'Иван Иванов',
            current_balance: -50.0,
            total_due: 100.0,
            total_paid: 50.0,
            recent_payments: [],
          },
        };
        mockGet.mockResolvedValueOnce(mockSummary);

        const result = await paymentsApi.getApartmentSummary(1);

        expect(mockGet).toHaveBeenCalledWith('/payments/apartment/1/summary');
        expect(result).toEqual(mockSummary.data);
      });
    });

    describe('delete', () => {
      it('should delete payment', async () => {
        mockDelete.mockResolvedValueOnce({ data: null });

        await paymentsApi.delete(1);

        expect(mockDelete).toHaveBeenCalledWith('/payments/1');
      });
    });
  });

  // =========================================================================
  // Obligations API Tests
  // =========================================================================
  describe('obligationsApi', () => {
    describe('getAll', () => {
      it('should fetch all obligations without filters', async () => {
        const mockObligations = {
          data: [
            { id: 1, amount: 10, type: 'monthly', apartment_id: 1, month: '2026-01' },
          ],
        };
        mockGet.mockResolvedValueOnce(mockObligations);

        const result = await obligationsApi.getAll();

        expect(mockGet).toHaveBeenCalledWith('/obligations?');
        expect(result).toEqual(mockObligations.data);
      });

      it('should fetch obligations with filters', async () => {
        const mockObligations = { data: [] };
        mockGet.mockResolvedValueOnce(mockObligations);

        await obligationsApi.getAll({
          apartment_id: 1,
          type: 'monthly',
          month: '2026-01',
          skip: 5,
          limit: 10,
        });

        // Note: skip=0 would not appear in URL because 0 is falsy
        expect(mockGet).toHaveBeenCalledWith(
          '/obligations?skip=5&limit=10&type=monthly&apartment_id=1&month=2026-01'
        );
      });

      it('should fetch obligations with partial filters', async () => {
        const mockObligations = { data: [] };
        mockGet.mockResolvedValueOnce(mockObligations);

        await obligationsApi.getAll({ type: 'penalty' });

        expect(mockGet).toHaveBeenCalledWith('/obligations?type=penalty');
      });
    });

    describe('getById', () => {
      it('should fetch obligation by id', async () => {
        const mockObligation = {
          data: { id: 1, amount: 10, type: 'monthly', apartment_id: 1 },
        };
        mockGet.mockResolvedValueOnce(mockObligation);

        const result = await obligationsApi.getById(1);

        expect(mockGet).toHaveBeenCalledWith('/obligations/1');
        expect(result).toEqual(mockObligation.data);
      });
    });

    describe('create', () => {
      it('should create new obligation', async () => {
        const obligationData = {
          apartment_id: 1,
          amount: 10.0,
          type: 'monthly' as const,
          month: '2026-01',
          description: 'Месечна такса',
        };
        const mockResponse = {
          data: {
            id: 1,
            ...obligationData,
            created_at: '2026-01-01T00:00:00',
            paid_amount: 0,
            is_paid: false,
          },
        };
        mockPost.mockResolvedValueOnce(mockResponse);

        const result = await obligationsApi.create(obligationData);

        // Note: obligations API uses trailing slash
        expect(mockPost).toHaveBeenCalledWith('/obligations/', obligationData);
        expect(result).toEqual(mockResponse.data);
      });

      it('should handle validation error on create', async () => {
        const error = {
          response: {
            status: 422,
            data: { detail: 'Invalid obligation type' },
          },
        };
        mockPost.mockRejectedValueOnce(error);

        await expect(
          obligationsApi.create({ amount: 10, type: 'invalid' as any } as any)
        ).rejects.toEqual(error);
      });
    });

    describe('update', () => {
      it('should update existing obligation', async () => {
        const updateData = { amount: 15.0 };
        const mockResponse = {
          data: { id: 1, amount: 15.0, type: 'monthly', apartment_id: 1 },
        };
        mockPatch.mockResolvedValueOnce(mockResponse);

        const result = await obligationsApi.update(1, updateData);

        expect(mockPatch).toHaveBeenCalledWith('/obligations/1', updateData);
        expect(result).toEqual(mockResponse.data);
      });
    });

    describe('delete', () => {
      it('should delete obligation', async () => {
        mockDelete.mockResolvedValueOnce({ data: null });

        await obligationsApi.delete(1);

        expect(mockDelete).toHaveBeenCalledWith('/obligations/1');
      });
    });

    describe('getByApartment', () => {
      it('should fetch obligations by apartment', async () => {
        const mockObligations = {
          data: [
            { id: 1, amount: 10, type: 'monthly', apartment_id: 5 },
            { id: 2, amount: 20, type: 'repair', apartment_id: 5 },
          ],
        };
        mockGet.mockResolvedValueOnce(mockObligations);

        const result = await obligationsApi.getByApartment(5);

        expect(mockGet).toHaveBeenCalledWith('/obligations/apartment/5');
        expect(result).toEqual(mockObligations.data);
      });
    });

    describe('getApartmentBalance', () => {
      it('should fetch apartment balance', async () => {
        const mockBalance = {
          data: {
            apartment_id: 1,
            total_due: 100.0,
            total_paid: 50.0,
            balance: -50.0,
          },
        };
        mockGet.mockResolvedValueOnce(mockBalance);

        const result = await obligationsApi.getApartmentBalance(1);

        expect(mockGet).toHaveBeenCalledWith('/obligations/apartment/1/balance');
        expect(result).toEqual(mockBalance.data);
      });
    });

    describe('generateMonthly', () => {
      it('should generate monthly obligations', async () => {
        const mockObligations = {
          data: [
            { id: 1, amount: 10, type: 'monthly', apartment_id: 1, month: '2026-02' },
            { id: 2, amount: 10, type: 'monthly', apartment_id: 2, month: '2026-02' },
          ],
        };
        mockPost.mockResolvedValueOnce(mockObligations);

        const result = await obligationsApi.generateMonthly('2026-02');

        expect(mockPost).toHaveBeenCalledWith('/obligations/generate-monthly?month=2026-02');
        expect(result).toEqual(mockObligations.data);
      });
    });

    describe('getSummary', () => {
      it('should fetch obligations summary', async () => {
        const mockSummary = {
          data: {
            total_obligations: 1000.0,
            total_paid: 750.0,
            total_outstanding: 250.0,
          },
        };
        mockGet.mockResolvedValueOnce(mockSummary);

        const result = await obligationsApi.getSummary();

        expect(mockGet).toHaveBeenCalledWith('/obligations/stats/summary?');
        expect(result).toEqual(mockSummary.data);
      });

      it('should fetch summary with filters', async () => {
        const mockSummary = { data: {} };
        mockGet.mockResolvedValueOnce(mockSummary);

        await obligationsApi.getSummary({
          apartment_id: 1,
          month: '2026-01',
          type: 'monthly',
        });

        expect(mockGet).toHaveBeenCalledWith(
          '/obligations/stats/summary?apartment_id=1&month=2026-01&type=monthly'
        );
      });
    });

    describe('getMonthlySummary', () => {
      it('should fetch monthly summary', async () => {
        const mockSummary = {
          data: {
            month: '2026-01',
            total_due: 500.0,
            total_paid: 300.0,
            apartments_count: 20,
          },
        };
        mockGet.mockResolvedValueOnce(mockSummary);

        const result = await obligationsApi.getMonthlySummary('2026-01');

        expect(mockGet).toHaveBeenCalledWith('/obligations/stats/monthly/2026-01');
        expect(result).toEqual(mockSummary.data);
      });
    });
  });

  // =========================================================================
  // Dashboard API Tests
  // =========================================================================
  describe('dashboardApi', () => {
    describe('getDashboard', () => {
      it('should fetch dashboard without month parameter', async () => {
        const mockDashboard = {
          data: {
            current_month: '2026-01',
            total_apartments: 20,
            total_due: 200.0,
            total_paid: 150.0,
            collection_rate: 75.0,
            recent_payments: [],
            apartments_with_debt: [],
          },
        };
        mockGet.mockResolvedValueOnce(mockDashboard);

        const result = await dashboardApi.getDashboard();

        expect(mockGet).toHaveBeenCalledWith('/dashboard');
        expect(result).toEqual(mockDashboard.data);
      });

      it('should fetch dashboard with specific month', async () => {
        const mockDashboard = {
          data: {
            current_month: '2026-02',
            total_apartments: 20,
            total_due: 200.0,
            total_paid: 100.0,
            collection_rate: 50.0,
            recent_payments: [],
            apartments_with_debt: [],
          },
        };
        mockGet.mockResolvedValueOnce(mockDashboard);

        const result = await dashboardApi.getDashboard('2026-02');

        expect(mockGet).toHaveBeenCalledWith('/dashboard?month=2026-02');
        expect(result).toEqual(mockDashboard.data);
      });
    });

    describe('getFundBalance', () => {
      it('should fetch fund balance', async () => {
        const mockFund = {
          data: {
            current_balance: 5000.0,
            total_income: 10000.0,
            total_expenses: 5000.0,
          },
        };
        mockGet.mockResolvedValueOnce(mockFund);

        const result = await dashboardApi.getFundBalance();

        expect(mockGet).toHaveBeenCalledWith('/dashboard/fund');
        expect(result).toEqual(mockFund.data);
      });
    });
  });

  // =========================================================================
  // Receipts API Tests
  // =========================================================================
  describe('receiptsApi', () => {
    describe('downloadPdf', () => {
      beforeEach(() => {
        // Mock window and document APIs for download
        vi.stubGlobal('URL', {
          createObjectURL: vi.fn(() => 'blob:test-url'),
          revokeObjectURL: vi.fn(),
        });
        
        const mockLink = {
          href: '',
          setAttribute: vi.fn(),
          click: vi.fn(),
          remove: vi.fn(),
        };
        vi.stubGlobal('document', {
          createElement: vi.fn(() => mockLink),
          body: {
            appendChild: vi.fn(),
          },
        });
      });

      it('should download receipt PDF', async () => {
        const mockBlobData = new ArrayBuffer(100);
        const mockResponse = {
          data: mockBlobData,
          headers: {
            'content-disposition': 'attachment; filename="receipt-2026-000001.pdf"',
          },
        };
        mockGet.mockResolvedValueOnce(mockResponse);

        await receiptsApi.downloadPdf(1);

        expect(mockGet).toHaveBeenCalledWith('/receipts/1/pdf', {
          responseType: 'blob',
        });
        expect(URL.createObjectURL).toHaveBeenCalled();
        expect(document.createElement).toHaveBeenCalledWith('a');
      });

      it('should use default filename when content-disposition is missing', async () => {
        const mockBlobData = new ArrayBuffer(100);
        const mockResponse = {
          data: mockBlobData,
          headers: {},
        };
        mockGet.mockResolvedValueOnce(mockResponse);

        await receiptsApi.downloadPdf(1);

        expect(mockGet).toHaveBeenCalledWith('/receipts/1/pdf', {
          responseType: 'blob',
        });
      });

      it('should handle download error', async () => {
        const error = {
          response: {
            status: 404,
            data: { detail: 'Receipt not found' },
          },
        };
        mockGet.mockRejectedValueOnce(error);

        await expect(receiptsApi.downloadPdf(999)).rejects.toEqual(error);
      });
    });
  });

  // =========================================================================
  // Error Handling Tests
  // =========================================================================
  describe('Error Handling', () => {
    describe('401 Unauthorized', () => {
      it('should reject with 401 error for expired token', async () => {
        const error = {
          response: {
            status: 401,
            data: { detail: 'Could not validate credentials' },
          },
        };
        mockGet.mockRejectedValueOnce(error);

        await expect(authApi.getMe()).rejects.toEqual(error);
        expect(error.response.status).toBe(401);
      });

      it('should reject with 401 for invalid login', async () => {
        const error = {
          response: {
            status: 401,
            data: { detail: 'Incorrect username or password' },
          },
        };
        mockPost.mockRejectedValueOnce(error);

        await expect(authApi.login('invalid', 'wrong')).rejects.toEqual(error);
      });
    });

    describe('500 Server Error', () => {
      it('should reject with 500 error for server failure', async () => {
        const error = {
          response: {
            status: 500,
            data: { detail: 'Internal server error' },
          },
        };
        mockGet.mockRejectedValueOnce(error);

        await expect(apartmentsApi.getAll()).rejects.toEqual(error);
        expect(error.response.status).toBe(500);
      });

      it('should reject with 500 on payment creation server error', async () => {
        const error = {
          response: {
            status: 500,
            data: { detail: 'Database error' },
          },
        };
        mockPost.mockRejectedValueOnce(error);

        await expect(
          paymentsApi.create({
            apartment_id: 1,
            amount: 50,
            month: '2026-01',
            payment_method: 'cash',
          })
        ).rejects.toEqual(error);
      });
    });

    describe('404 Not Found', () => {
      it('should reject with 404 for non-existent resource', async () => {
        const error = {
          response: {
            status: 404,
            data: { detail: 'Not found' },
          },
        };
        mockGet.mockRejectedValueOnce(error);

        await expect(apartmentsApi.getById(9999)).rejects.toEqual(error);
      });

      it('should reject with 404 for non-existent payment', async () => {
        const error = {
          response: {
            status: 404,
            data: { detail: 'Payment not found' },
          },
        };
        mockGet.mockRejectedValueOnce(error);

        await expect(paymentsApi.getById(9999)).rejects.toEqual(error);
      });

      it('should reject with 404 for non-existent obligation', async () => {
        const error = {
          response: {
            status: 404,
            data: { detail: 'Obligation not found' },
          },
        };
        mockGet.mockRejectedValueOnce(error);

        await expect(obligationsApi.getById(9999)).rejects.toEqual(error);
      });
    });

    describe('422 Validation Error', () => {
      it('should reject with 422 for invalid data', async () => {
        const error = {
          response: {
            status: 422,
            data: {
              detail: [
                {
                  loc: ['body', 'amount'],
                  msg: 'value is not a valid float',
                  type: 'type_error.float',
                },
              ],
            },
          },
        };
        mockPost.mockRejectedValueOnce(error);

        await expect(
          paymentsApi.create({ amount: 'invalid' } as any)
        ).rejects.toEqual(error);
      });

      it('should reject with 422 for missing required fields', async () => {
        const error = {
          response: {
            status: 422,
            data: {
              detail: [
                {
                  loc: ['body', 'apartment_id'],
                  msg: 'field required',
                  type: 'value_error.missing',
                },
              ],
            },
          },
        };
        mockPost.mockRejectedValueOnce(error);

        await expect(
          obligationsApi.create({ amount: 10 } as any)
        ).rejects.toEqual(error);
      });
    });

    describe('Network Errors', () => {
      it('should reject on network failure', async () => {
        const error = new Error('Network Error');
        mockGet.mockRejectedValueOnce(error);

        await expect(dashboardApi.getDashboard()).rejects.toEqual(error);
      });

      it('should reject on timeout', async () => {
        const error = {
          code: 'ECONNABORTED',
          message: 'timeout of 30000ms exceeded',
        };
        mockGet.mockRejectedValueOnce(error);

        await expect(apartmentsApi.getAll()).rejects.toEqual(error);
      });
    });
  });
});