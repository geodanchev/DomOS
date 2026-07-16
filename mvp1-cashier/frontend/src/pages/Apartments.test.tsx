import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ThemeProvider } from '../context/ThemeContext';
import Apartments from './Apartments';
import type { Apartment, ApartmentList, User, UIPermissions } from '../types';

// =============================================================================
// Mock API
// =============================================================================
vi.mock('../services/api', () => ({
  apartmentsApi: {
    getAll: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  obligationsApi: {
    getAll: vi.fn(),
  },
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
  },
}));

// Mock useToast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

import { apartmentsApi } from '../services/api';

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
  apartments: { view: true, create: true, edit: true, delete: true },
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
    notes: 'Първи етаж',
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
  {
    id: 3,
    number: '3А',
    floor: 2,
    owner_name: 'Мария Георгиева',
    residents_count: 4,
    monthly_fee: 60.00,
    notes: 'Ъглов апартамент',
    created_at: '2026-01-03T00:00:00Z',
    updated_at: '2026-01-03T00:00:00Z',
  },
];

const mockApartmentList: ApartmentList = {
  items: mockApartments,
  total: mockApartments.length,
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
describe('Apartments Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  describe('Apartments List Rendering', () => {
    it('should render apartments page with title', async () => {
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText(/домова книга/i)).toBeInTheDocument();
      });
    });

    it('should render apartments table with headers', async () => {
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for table headers
      await waitFor(() => {
        expect(screen.getByText('№')).toBeInTheDocument();
        expect(screen.getByText(/собственик/i)).toBeInTheDocument();
      });
    });

    it('should render all apartments from the list', async () => {
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for apartments to load
      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
        expect(screen.getByText('Петър Петров')).toBeInTheDocument();
        expect(screen.getByText('Мария Георгиева')).toBeInTheDocument();
      });
    });

    it('should render apartment count stats', async () => {
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for count to appear
      await waitFor(() => {
        expect(screen.getByText(/общо апартаменти/i)).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
      });
    });
  });

  describe('Apartment Numbers Display', () => {
    it('should display apartment numbers in the table', async () => {
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for apartment numbers
      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('3А')).toBeInTheDocument();
      });
    });

    it('should display apartment numbers with alphanumeric characters', async () => {
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Check for alphanumeric apartment number
      await waitFor(() => {
        expect(screen.getByText('3А')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner while data is loading', async () => {
      // Create a promise that never resolves during the check
      let resolveApartments: (value: ApartmentList) => void;
      const apartmentsPromise = new Promise<ApartmentList>((resolve) => {
        resolveApartments = resolve;
      });
      vi.mocked(apartmentsApi.getAll).mockReturnValueOnce(apartmentsPromise);

      renderWithProviders(<Apartments />);

      // Check for loading state (Loader2 spinner has animate-spin class)
      expect(document.querySelector('.animate-spin')).toBeInTheDocument();

      // Resolve to clean up
      resolveApartments!(mockApartmentList);

      await waitFor(() => {
        expect(screen.getByText(/домова книга/i)).toBeInTheDocument();
      });
    });

    it('should hide loading spinner after data loads', async () => {
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByText(/домова книга/i)).toBeInTheDocument();
      });

      // Main content should be visible
      expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should display empty message when no apartments exist', async () => {
      const emptyList: ApartmentList = {
        items: [],
        total: 0,
      };
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(emptyList);

      renderWithProviders(<Apartments />);

      // Wait for empty message
      await waitFor(() => {
        expect(screen.getByText(/няма добавени апартаменти/i)).toBeInTheDocument();
      });
    });
  });

  describe('Add Apartment Button', () => {
    it('should render add apartment button', async () => {
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for data to load first
      await waitFor(() => {
        expect(screen.getByText(/домова книга/i)).toBeInTheDocument();
      });

      // Check for add button
      expect(screen.getByRole('button', { name: /добави/i })).toBeInTheDocument();
    });

    it('should open dialog when add button is clicked', async () => {
      const user = userEvent.setup();
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText(/домова книга/i)).toBeInTheDocument();
      });

      // Click add button
      const addButton = screen.getByRole('button', { name: /добави/i });
      await user.click(addButton);

      // Dialog should open
      await waitFor(() => {
        expect(screen.getByText(/добавяне на апартамент/i)).toBeInTheDocument();
      });
    });
  });

  describe('Monthly Fee Display', () => {
    it('should display monthly fees for apartments (desktop view)', async () => {
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for monthly fees to appear
      await waitFor(() => {
        // Fees are displayed with formatting like "50.00 лв."
        expect(screen.getByText('50.00 лв.')).toBeInTheDocument();
        expect(screen.getByText('45.00 лв.')).toBeInTheDocument();
        expect(screen.getByText('60.00 лв.')).toBeInTheDocument();
      });
    });
  });

  describe('API Calls', () => {
    it('should call apartmentsApi.getAll on mount', async () => {
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      await waitFor(() => {
        expect(apartmentsApi.getAll).toHaveBeenCalled();
      });
    });
  });

  describe('Edit Apartment', () => {
    it('should show edit button for each apartment', async () => {
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
      });

      // Check for edit buttons (should be 3 - one per apartment)
      const editButtons = screen.getAllByTitle(/редактирай/i);
      expect(editButtons.length).toBe(3);
    });

    it('should open edit dialog when edit button is clicked', async () => {
      const user = userEvent.setup();
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
      });

      // Click first edit button
      const editButtons = screen.getAllByTitle(/редактирай/i);
      await user.click(editButtons[0]);

      // Dialog should open with edit title
      await waitFor(() => {
        expect(screen.getByText(/редактиране на апартамент/i)).toBeInTheDocument();
      });
    });
  });

  describe('Delete Apartment', () => {
    it('should show delete button for each apartment', async () => {
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
      });

      // Check for delete buttons (should be 3 - one per apartment)
      const deleteButtons = screen.getAllByTitle(/изтрий/i);
      expect(deleteButtons.length).toBe(3);
    });

    it('should open confirmation dialog when delete button is clicked', async () => {
      const user = userEvent.setup();
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
      });

      // Click first delete button
      const deleteButtons = screen.getAllByTitle(/изтрий/i);
      await user.click(deleteButtons[0]);

      // Confirmation dialog should open
      await waitFor(() => {
        expect(screen.getByText(/изтриване на апартамент/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation', () => {
    it('should show validation in dialog when adding apartment', async () => {
      const user = userEvent.setup();
      vi.mocked(apartmentsApi.getAll).mockResolvedValueOnce(mockApartmentList);

      renderWithProviders(<Apartments />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText(/домова книга/i)).toBeInTheDocument();
      });

      // Open add dialog
      const addButton = screen.getByRole('button', { name: /добави/i });
      await user.click(addButton);

      // Wait for dialog to open
      await waitFor(() => {
        expect(screen.getByText(/добавяне на апартамент/i)).toBeInTheDocument();
      });

      // Check for required fields
      expect(screen.getByLabelText(/номер на апартамент/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/име на собственик/i)).toBeInTheDocument();
    });
  });
});