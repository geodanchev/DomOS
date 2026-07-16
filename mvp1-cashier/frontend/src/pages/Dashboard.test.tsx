import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ThemeProvider } from '../context/ThemeContext';
import Dashboard from './Dashboard';
import type { CashierDashboard, FundBalance, User, UIPermissions } from '../types';

// =============================================================================
// Mock API
// =============================================================================
vi.mock('../services/api', () => ({
  dashboardApi: {
    getDashboard: vi.fn(),
    getFundBalance: vi.fn(),
  },
  obligationsApi: {
    getAll: vi.fn(),
  },
  apartmentsApi: {
    getAll: vi.fn(),
  },
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
  },
}));

import { dashboardApi } from '../services/api';

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

const mockDashboard: CashierDashboard = {
  current_month: '2026-07',
  total_apartments: 10,
  total_collected: 1500.00,
  total_owed: 500.00,
  collection_rate: 75,
  paid_count: 8,
  owes_count: 2,
  apartments: [
    {
      apartment_id: 1,
      apartment_number: '1',
      owner_name: 'Иван Иванов',
      balance: -100.00,
      total_obligations: 500.00,
      total_payments: 400.00,
      status: 'owes',
      status_display: 'Дължи 100 лв',
    },
    {
      apartment_id: 2,
      apartment_number: '2',
      owner_name: 'Петър Петров',
      balance: 0,
      total_obligations: 500.00,
      total_payments: 500.00,
      status: 'paid',
      status_display: 'Изплатен',
    },
    {
      apartment_id: 3,
      apartment_number: '3',
      owner_name: 'Мария Георгиева',
      balance: -200.00,
      total_obligations: 500.00,
      total_payments: 300.00,
      status: 'owes',
      status_display: 'Дължи 200 лв',
    },
  ],
};

const mockFundBalance: FundBalance = {
  current_balance: 5000.00,
  total_collected_all_time: 10000.00,
  total_expenses: 5000.00,
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
describe('Dashboard Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  describe('Dashboard Rendering', () => {
    it('should render dashboard with title after loading', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText(/табло/i)).toBeInTheDocument();
      });
    });

    it('should render month in title', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for month to appear (Юли 2026)
      await waitFor(() => {
        expect(screen.getByText(/юли 2026/i)).toBeInTheDocument();
      });
    });

    it('should render stats cards', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for stats to load
      await waitFor(() => {
        expect(screen.getByText(/баланс на фонда/i)).toBeInTheDocument();
        expect(screen.getByText(/общо събрани/i)).toBeInTheDocument();
        expect(screen.getByText(/общо дължимо/i)).toBeInTheDocument();
        expect(screen.getByText(/събираемост/i)).toBeInTheDocument();
      });
    });
  });

  describe('Balance Display', () => {
    it('should display fund balance correctly', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for fund balance to appear
      await waitFor(() => {
        expect(screen.getByText('5000.00 лв')).toBeInTheDocument();
      });
    });

    it('should display total collected amount', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for collected amount to appear
      await waitFor(() => {
        expect(screen.getByText('1500.00 лв')).toBeInTheDocument();
      });
    });

    it('should display total owed amount', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for owed amount to appear
      await waitFor(() => {
        expect(screen.getByText('500.00 лв')).toBeInTheDocument();
      });
    });

    it('should display collection rate percentage', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for collection rate to appear
      await waitFor(() => {
        expect(screen.getByText('75%')).toBeInTheDocument();
      });
    });

    it('should display paid/total count', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for paid count to appear
      await waitFor(() => {
        expect(screen.getByText('8 / 10')).toBeInTheDocument();
      });
    });
  });

  describe('Apartments with Obligations', () => {
    it('should display apartments with obligations section', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for section header
      await waitFor(() => {
        expect(screen.getByText(/апартаменти със задължения/i)).toBeInTheDocument();
      });
    });

    it('should display owner names for apartments with obligations', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for owner names (only those with owes status)
      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
        expect(screen.getByText('Мария Георгиева')).toBeInTheDocument();
      });
    });

    it('should display obligation amounts', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for amounts (absolute values)
      await waitFor(() => {
        expect(screen.getByText('100.00 лв')).toBeInTheDocument();
        expect(screen.getByText('200.00 лв')).toBeInTheDocument();
      });
    });

    it('should show no obligations message when all paid', async () => {
      const allPaidDashboard: CashierDashboard = {
        ...mockDashboard,
        owes_count: 0,
        apartments: mockDashboard.apartments.map(apt => ({
          ...apt,
          balance: 0,
          status: 'paid' as const,
        })),
      };
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(allPaidDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for no obligations message
      await waitFor(() => {
        expect(screen.getByText(/няма апартаменти със задължения/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner while data is loading', async () => {
      // Create a promise that never resolves during the check
      let resolveDashboard: (value: CashierDashboard) => void;
      const dashboardPromise = new Promise<CashierDashboard>((resolve) => {
        resolveDashboard = resolve;
      });
      vi.mocked(dashboardApi.getDashboard).mockReturnValueOnce(dashboardPromise);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Check for loading state (Loader2 spinner has animate-spin class)
      expect(document.querySelector('.animate-spin')).toBeInTheDocument();

      // Resolve to clean up
      resolveDashboard!(mockDashboard);

      await waitFor(() => {
        expect(screen.getByText(/табло/i)).toBeInTheDocument();
      });
    });

    it('should hide loading spinner after data loads', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByText(/табло/i)).toBeInTheDocument();
      });

      // Spinner should be gone (or at least the main content should be visible)
      expect(screen.queryByText(/зареждане/i)).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error message on API failure', async () => {
      vi.mocked(dashboardApi.getDashboard).mockRejectedValueOnce(new Error('API Error'));
      vi.mocked(dashboardApi.getFundBalance).mockRejectedValueOnce(new Error('API Error'));

      renderWithProviders(<Dashboard />);

      // Wait for error message
      await waitFor(() => {
        expect(screen.getByText(/грешка при зареждане/i)).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      vi.mocked(dashboardApi.getDashboard).mockRejectedValueOnce(new Error('API Error'));
      vi.mocked(dashboardApi.getFundBalance).mockRejectedValueOnce(new Error('API Error'));

      renderWithProviders(<Dashboard />);

      // Wait for retry button
      await waitFor(() => {
        expect(screen.getByText(/опитай пак/i)).toBeInTheDocument();
      });
    });
  });

  describe('Quick Stats Badges', () => {
    it('should display paid count badge', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/изплатени: 8/i)).toBeInTheDocument();
      });
    });

    it('should display owes count badge', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/дължат: 2/i)).toBeInTheDocument();
      });
    });
  });

  describe('API Calls', () => {
    it('should call dashboard and fund APIs on mount', async () => {
      vi.mocked(dashboardApi.getDashboard).mockResolvedValueOnce(mockDashboard);
      vi.mocked(dashboardApi.getFundBalance).mockResolvedValueOnce(mockFundBalance);

      renderWithProviders(<Dashboard />);

      await waitFor(() => {
        expect(dashboardApi.getDashboard).toHaveBeenCalled();
        expect(dashboardApi.getFundBalance).toHaveBeenCalled();
      });
    });
  });
});