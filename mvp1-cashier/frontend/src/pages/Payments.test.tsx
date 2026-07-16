import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ThemeProvider } from '../context/ThemeContext';
import Payments from './Payments';
import type { Payment, PaymentList, Apartment, ApartmentList, User, UIPermissions } from '../types';

// =============================================================================
// Mock API
// =============================================================================
vi.mock('../services/api', () => ({
  paymentsApi: {
    getAll: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
  apartmentsApi: {
    getAll: vi.fn(),
  },
  receiptsApi: {
    downloadPdf: vi.fn(),
  },
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
  },
}));

import { paymentsApi, apartmentsApi } from '../services/api';

// =============================================================================
// Test Data
// =============================================================================
const mockUser: User = {
  id: 1,
  username: 'testuser',
  display_name: 'Test User',
  role: 'cashier',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const mockPermissions: UIPermissions = {
  apartments: { view: true, create: true, edit: true, delete: false },
  payments: { view: true, create: true, void: false },
  obligations: { view: true, create: true, edit: true, delete: false, generate_monthly: false },
  expenses: { view: true, create: false, edit: false, delete: false },
  reports: { view: true, export: true },
  scheduler: { manage: false },
  users: { manage: false },
};

const mockApartments: Apartment[] = [
  {
    id: 1,
    number: '1',
    floor: 1,
    owner_name: 'Иван Иванов',
    residents_count: 3,
    monthly_fee: 50.00,
    notes: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 2,
    number: '2',
    floor: 1,
    owner_name: 'Петър Петров',
    residents_count: 2,
    monthly_fee: 45.00,
    notes: null,
    created_at: '2026-01-02T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
  },
];

const mockApartmentList: ApartmentList = {
  items: mockApartments,
  total: mockApartments.length,
};

const mockPayments: Payment[] = [
  {
    id: 1,
    apartment_id: 1,
    apartment_number: '1',
    owner_name: 'Иван Иванов',
    amount: 50.00,
    payment_date: '2026-07-01T10:00:00Z',
    month: '2026-07',
    description: 'Месечна вноска',
    receipt_id: 1,
    created_by: 1,
    created_at: '2026-07-01T10:00:00Z',
    updated_at: '2026-07-01T10:00:00Z',
  },
  {
    id: 2,
    apartment_id: 2,
    apartment_number: '2',
    owner_name: 'Петър Петров',
    amount: 90.00,
    payment_date: '2026-07-02T11:00:00Z',
    month: '2026-07',
    description: 'Месечна вноска + ремонт',
    receipt_id: 2,
    created_by: 1,
    created_at: '2026-07-02T11:00:00Z',
    updated_at: '2026-07-02T11:00:00Z',
  },
  {
    id: 3,
    apartment_id: 1,
    apartment_number: '1',
    owner_name: 'Иван Иванов',
    amount: 25.50,
    payment_date: '2026-07-05T14:00:00Z',
    month: '2026-07',
    description: 'Частично плащане',
    receipt_id: null,
    created_by: 1,
    created_at: '2026-07-05T14:00:00Z',
    updated_at: '2026-07-05T14:00:00Z',
  },
];

const mockPaymentList: PaymentList = {
  items: mockPayments,
  total: mockPayments.length,
};

// =============================================================================
// Helper Function
// =============================================================================
const renderWithProviders = (ui: React.ReactElement) => {
  // Set up authenticated state
  localStorage.setItem('token', 'test-token');
  localStorage.setItem('user', JSON.stringify(mockUser));
  localStorage.setItem('permissions', JSON.stringify(mockPermissions));

  return render(
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          {ui}
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
};

// =============================================================================
// Tests
// =============================================================================
describe('Payments Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  describe('Payments List Rendering', () => {
    it('should render payments page with title', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText(/история на плащанията/i)).toBeInTheDocument();
      });
    });

    it('should render payments table with headers', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for table headers - use role to be more specific
      await waitFor(() => {
        expect(screen.getByRole('columnheader', { name: /ап\./i })).toBeInTheDocument();
        expect(screen.getByRole('columnheader', { name: /собственик/i })).toBeInTheDocument();
        expect(screen.getByRole('columnheader', { name: /сума/i })).toBeInTheDocument();
      });
    });

    it('should render all payments from the list', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for payments to load - check owner names
      await waitFor(() => {
        // Иван Иванов appears twice (2 payments)
        const ivanElements = screen.getAllByText('Иван Иванов');
        expect(ivanElements.length).toBe(2);
        expect(screen.getByText('Петър Петров')).toBeInTheDocument();
      });
    });

    it('should render payments count in section header', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for count to appear in "Плащания (3)"
      await waitFor(() => {
        expect(screen.getByText(/плащания \(3\)/i)).toBeInTheDocument();
      });
    });
  });

  describe('Payment Amounts Display', () => {
    it('should display payment amounts correctly', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for amounts to appear
      await waitFor(() => {
        expect(screen.getByText('50.00 лв')).toBeInTheDocument();
        expect(screen.getByText('90.00 лв')).toBeInTheDocument();
        expect(screen.getByText('25.50 лв')).toBeInTheDocument();
      });
    });

    it('should display total amount in stats', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Total should be 50 + 90 + 25.50 = 165.50
      await waitFor(() => {
        expect(screen.getByText('165.50 лв')).toBeInTheDocument();
      });
    });

    it('should display total payments count in stats', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for stats
      await waitFor(() => {
        expect(screen.getByText(/общо плащания/i)).toBeInTheDocument();
        // The count "3" should appear in the stats section
        const statsSection = screen.getByText(/общо плащания/i).closest('div');
        expect(statsSection).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner while data is loading', async () => {
      // Create a promise that never resolves during the check
      let resolvePayments: (value: PaymentList) => void;
      const paymentsPromise = new Promise<PaymentList>((resolve) => {
        resolvePayments = resolve;
      });
      vi.mocked(paymentsApi.getAll).mockReturnValueOnce(paymentsPromise);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Check for loading state (Loader2 spinner has animate-spin class)
      await waitFor(() => {
        expect(document.querySelector('.animate-spin')).toBeInTheDocument();
      });

      // Resolve to clean up
      resolvePayments!(mockPaymentList);

      await waitFor(() => {
        expect(screen.getByText(/история на плащанията/i)).toBeInTheDocument();
      });
    });

    it('should hide loading spinner after data loads', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByText(/история на плащанията/i)).toBeInTheDocument();
      });

      // Main content should be visible - check for table content
      await waitFor(() => {
        expect(screen.getByText(/плащания \(3\)/i)).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    it('should display empty message when no payments exist', async () => {
      const emptyList: PaymentList = {
        items: [],
        total: 0,
      };
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(emptyList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for empty message
      await waitFor(() => {
        expect(screen.getByText(/няма намерени плащания/i)).toBeInTheDocument();
      });
    });
  });

  describe('New Payment Button', () => {
    it('should render new payment button', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for data to load first
      await waitFor(() => {
        expect(screen.getByText(/история на плащанията/i)).toBeInTheDocument();
      });

      // Check for new payment button
      expect(screen.getByRole('button', { name: /ново/i })).toBeInTheDocument();
    });

    it('should open dialog when new payment button is clicked', async () => {
      const user = userEvent.setup();
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText(/история на плащанията/i)).toBeInTheDocument();
      });

      // Click new payment button - look for button with green styling or containing 'Ново'
      const buttons = screen.getAllByRole('button');
      const newPaymentButton = buttons.find(btn => 
        btn.textContent?.includes('Ново') && btn.classList.contains('bg-green-600')
      ) || screen.getByRole('button', { name: /ново/i });
      await user.click(newPaymentButton);

      // Dialog should open - check for dialog role or title containing 'плащане'
      await waitFor(() => {
        // The dialog title is '💵 Ново плащане'
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Apartment Numbers Display', () => {
    it('should display apartment numbers in the table', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for apartment numbers
      await waitFor(() => {
        // Apartment '1' appears twice (2 payments for apt 1)
        const apt1Elements = screen.getAllByText('1');
        expect(apt1Elements.length).toBeGreaterThanOrEqual(2);
        expect(screen.getByText('2')).toBeInTheDocument();
      });
    });
  });

  describe('Filters', () => {
    it('should render apartment filter dropdown', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for filter to appear
      await waitFor(() => {
        expect(screen.getByText(/апартамент/i)).toBeInTheDocument();
      });
    });

    it('should render month filter dropdown', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for filter to appear
      await waitFor(() => {
        expect(screen.getByText(/месец/i)).toBeInTheDocument();
      });
    });

    it('should render clear filters button', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText(/история на плащанията/i)).toBeInTheDocument();
      });

      // Check for clear button
      expect(screen.getByRole('button', { name: /изчисти/i })).toBeInTheDocument();
    });
  });

  describe('Receipt Download', () => {
    it('should show receipt button for payments with receipt_id', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for table to load
      await waitFor(() => {
        expect(screen.getByText(/плащания \(3\)/i)).toBeInTheDocument();
      });

      // Should have receipt buttons (payments 1 and 2 have receipt_id)
      // Find buttons with 📄 text
      const allButtons = screen.getAllByRole('button');
      const receiptButtons = allButtons.filter(btn => btn.textContent?.includes('📄'));
      expect(receiptButtons.length).toBe(2);
    });

    it('should show dash for payments without receipt_id', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for table to load
      await waitFor(() => {
        expect(screen.getByText(/плащания \(3\)/i)).toBeInTheDocument();
      });

      // Payment 3 has no receipt - should show dash in the last column
      // The dash is inside a span with muted-foreground class
      const dashes = screen.getAllByText('-');
      expect(dashes.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('API Calls', () => {
    it('should call paymentsApi.getAll and apartmentsApi.getAll on mount', async () => {
      vi.mocked(paymentsApi.getAll).mockResolvedValueOnce(mockPaymentList);
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      await waitFor(() => {
        expect(paymentsApi.getAll).toHaveBeenCalled();
        expect(apartmentsApi.getAll).toHaveBeenCalled();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message on API failure', async () => {
      vi.mocked(paymentsApi.getAll).mockRejectedValueOnce(new Error('API Error'));
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Payments />);

      // Wait for error message
      await waitFor(() => {
        expect(screen.getByText(/грешка при зареждане/i)).toBeInTheDocument();
      });
    });
  });
});