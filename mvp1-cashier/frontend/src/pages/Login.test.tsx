import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ThemeProvider } from '../context/ThemeContext';
import Login from './Login';
import type { LoginResponse, User, UIPermissions } from '../types';

// =============================================================================
// Mock react-router-dom
// =============================================================================
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// =============================================================================
// Mock API
// =============================================================================
vi.mock('../services/api', () => ({
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
  },
}));

import { authApi } from '../services/api';

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

const mockLoginResponse: LoginResponse = {
  access_token: 'test-token-12345',
  token_type: 'bearer',
  user: mockUser,
  permissions: mockPermissions,
};

// =============================================================================
// Helper Function
// =============================================================================
const renderWithProviders = (ui: React.ReactElement) => {
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
describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  describe('Form Rendering', () => {
    it('should render login form with all fields', () => {
      renderWithProviders(<Login />);

      // Check for title
      expect(screen.getByText('🏠 DomOS')).toBeInTheDocument();
      expect(screen.getByText('Дигитален касиер')).toBeInTheDocument();

      // Check for form fields
      expect(screen.getByLabelText(/потребителско име/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/парола/i)).toBeInTheDocument();

      // Check for submit button
      expect(screen.getByRole('button', { name: /вход/i })).toBeInTheDocument();
    });

    it('should render username and password inputs as required', () => {
      renderWithProviders(<Login />);

      const usernameInput = screen.getByLabelText(/потребителско име/i);
      const passwordInput = screen.getByLabelText(/парола/i);

      expect(usernameInput).toBeRequired();
      expect(passwordInput).toBeRequired();
    });

    it('should have password field with type password', () => {
      renderWithProviders(<Login />);

      const passwordInput = screen.getByLabelText(/парола/i);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });
  });

  describe('Successful Login', () => {
    it('should login successfully and navigate to home', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.login).mockResolvedValueOnce(mockLoginResponse);

      renderWithProviders(<Login />);

      // Fill in the form
      const usernameInput = screen.getByLabelText(/потребителско име/i);
      const passwordInput = screen.getByLabelText(/парола/i);
      const submitButton = screen.getByRole('button', { name: /вход/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Wait for navigation
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });

    it('should call authApi.login with correct credentials', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.login).mockResolvedValueOnce(mockLoginResponse);

      renderWithProviders(<Login />);

      const usernameInput = screen.getByLabelText(/потребителско име/i);
      const passwordInput = screen.getByLabelText(/парола/i);
      const submitButton = screen.getByRole('button', { name: /вход/i });

      await user.type(usernameInput, 'myuser');
      await user.type(passwordInput, 'mypass');
      await user.click(submitButton);

      await waitFor(() => {
        expect(authApi.login).toHaveBeenCalledWith('myuser', 'mypass');
      });
    });
  });

  describe('Login Error Handling', () => {
    it('should display error message on login failure', async () => {
      const user = userEvent.setup();
      const errorResponse = {
        response: {
          data: { detail: 'Невалидно потребителско име или парола' },
        },
      };
      vi.mocked(authApi.login).mockRejectedValueOnce(errorResponse);

      renderWithProviders(<Login />);

      const usernameInput = screen.getByLabelText(/потребителско име/i);
      const passwordInput = screen.getByLabelText(/парола/i);
      const submitButton = screen.getByRole('button', { name: /вход/i });

      await user.type(usernameInput, 'wronguser');
      await user.type(passwordInput, 'wrongpass');
      await user.click(submitButton);

      // Wait for error message
      await waitFor(() => {
        expect(screen.getByText('Невалидно потребителско име или парола')).toBeInTheDocument();
      });
    });

    it('should display default error message when no detail provided', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.login).mockRejectedValueOnce(new Error('Network error'));

      renderWithProviders(<Login />);

      const usernameInput = screen.getByLabelText(/потребителско име/i);
      const passwordInput = screen.getByLabelText(/парола/i);
      const submitButton = screen.getByRole('button', { name: /вход/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'testpass');
      await user.click(submitButton);

      // Wait for default error message
      await waitFor(() => {
        expect(screen.getByText(/грешка при вход/i)).toBeInTheDocument();
      });
    });

    it('should not navigate on login failure', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.login).mockRejectedValueOnce(new Error('Login failed'));

      renderWithProviders(<Login />);

      const usernameInput = screen.getByLabelText(/потребителско име/i);
      const passwordInput = screen.getByLabelText(/парола/i);
      const submitButton = screen.getByRole('button', { name: /вход/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'testpass');
      await user.click(submitButton);

      // Wait a bit and ensure navigate was not called
      await waitFor(() => {
        expect(screen.getByText(/грешка при вход/i)).toBeInTheDocument();
      });
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('should show loading state while logging in', async () => {
      const user = userEvent.setup();
      // Create a promise that we can control
      let resolveLogin: (value: LoginResponse) => void;
      const loginPromise = new Promise<LoginResponse>((resolve) => {
        resolveLogin = resolve;
      });
      vi.mocked(authApi.login).mockReturnValueOnce(loginPromise);

      renderWithProviders(<Login />);

      const usernameInput = screen.getByLabelText(/потребителско име/i);
      const passwordInput = screen.getByLabelText(/парола/i);
      const submitButton = screen.getByRole('button', { name: /вход/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'testpass');
      await user.click(submitButton);

      // Check loading state
      await waitFor(() => {
        expect(screen.getByText(/влизане/i)).toBeInTheDocument();
      });

      // Resolve the promise
      resolveLogin!(mockLoginResponse);

      // Wait for navigation after resolve
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });

    it('should disable submit button while loading', async () => {
      const user = userEvent.setup();
      // Create a promise that never resolves during test
      vi.mocked(authApi.login).mockImplementationOnce(
        () => new Promise(() => {}) // Never resolves
      );

      renderWithProviders(<Login />);

      const usernameInput = screen.getByLabelText(/потребителско име/i);
      const passwordInput = screen.getByLabelText(/парола/i);
      const submitButton = screen.getByRole('button', { name: /вход/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'testpass');
      await user.click(submitButton);

      // Check that button is disabled
      await waitFor(() => {
        const loadingButton = screen.getByRole('button', { name: /влизане/i });
        expect(loadingButton).toBeDisabled();
      });
    });
  });

  describe('Form Interaction', () => {
    it('should update username field on input', async () => {
      const user = userEvent.setup();
      renderWithProviders(<Login />);

      const usernameInput = screen.getByLabelText(/потребителско име/i);
      await user.type(usernameInput, 'myusername');

      expect(usernameInput).toHaveValue('myusername');
    });

    it('should update password field on input', async () => {
      const user = userEvent.setup();
      renderWithProviders(<Login />);

      const passwordInput = screen.getByLabelText(/парола/i);
      await user.type(passwordInput, 'mypassword');

      expect(passwordInput).toHaveValue('mypassword');
    });

    it('should clear error message on new form submission', async () => {
      const user = userEvent.setup();
      // First submission fails
      vi.mocked(authApi.login).mockRejectedValueOnce({
        response: { data: { detail: 'First error' } },
      });
      // Second submission succeeds
      vi.mocked(authApi.login).mockResolvedValueOnce(mockLoginResponse);

      renderWithProviders(<Login />);

      const usernameInput = screen.getByLabelText(/потребителско име/i);
      const passwordInput = screen.getByLabelText(/парола/i);
      const submitButton = screen.getByRole('button', { name: /вход/i });

      // First attempt - should fail
      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'testpass');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('First error')).toBeInTheDocument();
      });

      // Clear and retry
      await user.clear(usernameInput);
      await user.clear(passwordInput);
      await user.type(usernameInput, 'correctuser');
      await user.type(passwordInput, 'correctpass');
      await user.click(submitButton);

      // Error should be cleared during submission
      await waitFor(() => {
        expect(screen.queryByText('First error')).not.toBeInTheDocument();
      });
    });
  });
});
