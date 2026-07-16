import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from './AuthContext';
import type { LoginResponse, User, UIPermissions } from '../types';

// =============================================================================
// Mock API
// =============================================================================
vi.mock('../services/api', () => ({
  authApi: {
    login: vi.fn(),
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
// Test Component
// =============================================================================
function TestComponent() {
  const { user, token, permissions, isLoading, isAuthenticated, login, logout } = useAuth();

  return (
    <div>
      <div data-testid="is-loading">{isLoading ? 'loading' : 'not-loading'}</div>
      <div data-testid="is-authenticated">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      <div data-testid="user">{user ? user.username : 'no-user'}</div>
      <div data-testid="token">{token || 'no-token'}</div>
      <div data-testid="permissions-apartments-view">
        {permissions.apartments.view ? 'can-view' : 'cannot-view'}
      </div>
      <button
        data-testid="login-button"
        onClick={() => login('testuser', 'password123')}
      >
        Login
      </button>
      <button data-testid="logout-button" onClick={logout}>
        Logout
      </button>
    </div>
  );
}

// Wrapper for testing login errors
function TestComponentWithErrorHandling() {
  const { login, isAuthenticated } = useAuth();
  const [error, setError] = React.useState<string | null>(null);

  const handleLogin = async () => {
    try {
      await login('baduser', 'badpass');
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div>
      <div data-testid="is-authenticated">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      <div data-testid="error">{error || 'no-error'}</div>
      <button data-testid="login-button" onClick={handleLogin}>
        Login
      </button>
    </div>
  );
}

import React from 'react';

// =============================================================================
// Tests
// =============================================================================
describe('AuthContext', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Reset all mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  // ---------------------------------------------------------------------------
  // Initial State Tests
  // ---------------------------------------------------------------------------
  describe('initial state', () => {
    it('should start with isLoading true, then false after mount', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // After mount, isLoading should become false
      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });
    });

    it('should start not authenticated when no stored session', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });

      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('not-authenticated');
      expect(screen.getByTestId('user')).toHaveTextContent('no-user');
      expect(screen.getByTestId('token')).toHaveTextContent('no-token');
    });

    it('should have default restrictive permissions when not authenticated', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });

      // Default permissions allow view
      expect(screen.getByTestId('permissions-apartments-view')).toHaveTextContent('can-view');
    });
  });

  // ---------------------------------------------------------------------------
  // Session Restore Tests
  // ---------------------------------------------------------------------------
  describe('session restore from localStorage', () => {
    it('should restore session when token and user exist in localStorage', async () => {
      // Pre-populate localStorage
      localStorage.setItem('token', 'stored-token-abc');
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('permissions', JSON.stringify(mockPermissions));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });

      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('authenticated');
      expect(screen.getByTestId('user')).toHaveTextContent('testuser');
      expect(screen.getByTestId('token')).toHaveTextContent('stored-token-abc');
    });

    it('should restore permissions from localStorage', async () => {
      localStorage.setItem('token', 'stored-token-abc');
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('permissions', JSON.stringify(mockPermissions));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });

      expect(screen.getByTestId('permissions-apartments-view')).toHaveTextContent('can-view');
    });

    it('should not restore session if only token exists (no user)', async () => {
      localStorage.setItem('token', 'stored-token-abc');
      // No user stored

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });

      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('not-authenticated');
    });

    it('should use default permissions if stored permissions are invalid JSON', async () => {
      localStorage.setItem('token', 'stored-token-abc');
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('permissions', 'invalid-json{{{');

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });

      // Should be authenticated but with default permissions
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('authenticated');
      expect(screen.getByTestId('permissions-apartments-view')).toHaveTextContent('can-view');
    });
  });

  // ---------------------------------------------------------------------------
  // Login Tests
  // ---------------------------------------------------------------------------
  describe('login', () => {
    it('should authenticate user on successful login', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.login).mockResolvedValueOnce(mockLoginResponse);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });

      // Click login button
      await user.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('authenticated');
      });

      expect(screen.getByTestId('user')).toHaveTextContent('testuser');
      expect(screen.getByTestId('token')).toHaveTextContent('test-token-12345');
    });

    it('should store session in localStorage after login', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.login).mockResolvedValueOnce(mockLoginResponse);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });

      await user.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('authenticated');
      });

      // Check localStorage
      expect(localStorage.getItem('token')).toBe('test-token-12345');
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));
      expect(localStorage.getItem('permissions')).toBe(JSON.stringify(mockPermissions));
    });

    it('should call authApi.login with correct credentials', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.login).mockResolvedValueOnce(mockLoginResponse);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });

      await user.click(screen.getByTestId('login-button'));

      expect(authApi.login).toHaveBeenCalledWith('testuser', 'password123');
    });
  });

  // ---------------------------------------------------------------------------
  // Login Error Tests
  // ---------------------------------------------------------------------------
  describe('login error', () => {
    it('should throw error on login failure', async () => {
      const user = userEvent.setup();
      const loginError = new Error('Invalid credentials');
      vi.mocked(authApi.login).mockRejectedValueOnce(loginError);

      render(
        <AuthProvider>
          <TestComponentWithErrorHandling />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('not-authenticated');
      });

      await user.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Invalid credentials');
      });

      // Should remain not authenticated
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('not-authenticated');
    });

    it('should not modify localStorage on login failure', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.login).mockRejectedValueOnce(new Error('Login failed'));

      render(
        <AuthProvider>
          <TestComponentWithErrorHandling />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('not-authenticated');
      });

      await user.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Login failed');
      });

      // localStorage should remain empty
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });
  });

  // ---------------------------------------------------------------------------
  // Logout Tests
  // ---------------------------------------------------------------------------
  describe('logout', () => {
    it('should clear authentication state on logout', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.login).mockResolvedValueOnce(mockLoginResponse);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });

      // Login first
      await user.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('authenticated');
      });

      // Now logout
      await user.click(screen.getByTestId('logout-button'));

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('not-authenticated');
      });

      expect(screen.getByTestId('user')).toHaveTextContent('no-user');
      expect(screen.getByTestId('token')).toHaveTextContent('no-token');
    });

    it('should clear localStorage on logout', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.login).mockResolvedValueOnce(mockLoginResponse);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });

      // Login first
      await user.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('authenticated');
      });

      // Verify localStorage has data
      expect(localStorage.getItem('token')).toBe('test-token-12345');

      // Now logout
      await user.click(screen.getByTestId('logout-button'));

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('not-authenticated');
      });

      // localStorage should be cleared
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
      expect(localStorage.getItem('permissions')).toBeNull();
    });

    it('should reset to default permissions on logout', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.login).mockResolvedValueOnce(mockLoginResponse);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-loading')).toHaveTextContent('not-loading');
      });

      // Login first
      await user.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('authenticated');
      });

      // Now logout
      await user.click(screen.getByTestId('logout-button'));

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('not-authenticated');
      });

      // Default permissions should be restored (view: true for apartments)
      expect(screen.getByTestId('permissions-apartments-view')).toHaveTextContent('can-view');
    });
  });

  // ---------------------------------------------------------------------------
  // useAuth Hook Error Tests
  // ---------------------------------------------------------------------------
  describe('useAuth hook', () => {
    it('should throw error when used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestComponent />);
      }).toThrow('useAuth must be used within an AuthProvider');

      consoleSpy.mockRestore();
    });
  });
});