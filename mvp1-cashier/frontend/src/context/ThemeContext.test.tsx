import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, useTheme } from './ThemeContext';

// =============================================================================
// Constants
// =============================================================================
const STORAGE_KEY = 'domos-theme';

// =============================================================================
// Test Component
// =============================================================================
function TestComponent() {
  const { theme, setTheme, resolvedTheme } = useTheme();

  return (
    <div>
      <div data-testid="theme">{theme}</div>
      <div data-testid="resolved-theme">{resolvedTheme}</div>
      <button data-testid="set-light" onClick={() => setTheme('light')}>
        Set Light
      </button>
      <button data-testid="set-dark" onClick={() => setTheme('dark')}>
        Set Dark
      </button>
      <button data-testid="set-system" onClick={() => setTheme('system')}>
        Set System
      </button>
    </div>
  );
}

// =============================================================================
// Mock matchMedia helper
// =============================================================================
function mockMatchMedia(prefersDark: boolean) {
  const listeners: Array<(e: { matches: boolean }) => void> = [];
  
  const mediaQueryList = {
    matches: prefersDark,
    media: '(prefers-color-scheme: dark)',
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn((event: string, callback: (e: { matches: boolean }) => void) => {
      if (event === 'change') {
        listeners.push(callback);
      }
    }),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  };

  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => {
      if (query === '(prefers-color-scheme: dark)') {
        return mediaQueryList;
      }
      return {
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      };
    }),
  });

  return {
    mediaQueryList,
    simulateSystemThemeChange: (dark: boolean) => {
      mediaQueryList.matches = dark;
      listeners.forEach(listener => listener({ matches: dark }));
    },
  };
}

// =============================================================================
// Tests
// =============================================================================
describe('ThemeContext', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Reset document classes
    document.documentElement.classList.remove('light', 'dark');
    // Reset matchMedia to default (light system preference)
    mockMatchMedia(false);
  });

  afterEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('light', 'dark');
  });

  // ---------------------------------------------------------------------------
  // Default Theme Tests
  // ---------------------------------------------------------------------------
  describe('default theme', () => {
    it('should default to system theme when no stored preference', () => {
      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('theme')).toHaveTextContent('system');
    });

    it('should resolve to light when system prefers light', () => {
      mockMatchMedia(false); // System prefers light

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('theme')).toHaveTextContent('system');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light');
    });

    it('should resolve to dark when system prefers dark', () => {
      mockMatchMedia(true); // System prefers dark

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('theme')).toHaveTextContent('system');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark');
    });
  });

  // ---------------------------------------------------------------------------
  // setTheme Tests
  // ---------------------------------------------------------------------------
  describe('setTheme', () => {
    it('should change theme to dark when setTheme(dark) is called', async () => {
      const user = userEvent.setup();

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('theme')).toHaveTextContent('system');

      await user.click(screen.getByTestId('set-dark'));

      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark');
    });

    it('should change theme to light when setTheme(light) is called', async () => {
      const user = userEvent.setup();
      mockMatchMedia(true); // Start with dark system preference

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      // Initially system -> dark
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark');

      await user.click(screen.getByTestId('set-light'));

      expect(screen.getByTestId('theme')).toHaveTextContent('light');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light');
    });

    it('should change theme back to system when setTheme(system) is called', async () => {
      const user = userEvent.setup();
      mockMatchMedia(true); // System prefers dark

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      // Set to light first
      await user.click(screen.getByTestId('set-light'));
      expect(screen.getByTestId('theme')).toHaveTextContent('light');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light');

      // Change back to system
      await user.click(screen.getByTestId('set-system'));
      expect(screen.getByTestId('theme')).toHaveTextContent('system');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark');
    });
  });

  // ---------------------------------------------------------------------------
  // localStorage Persistence Tests
  // ---------------------------------------------------------------------------
  describe('localStorage persistence', () => {
    it('should save theme to localStorage when setTheme is called', async () => {
      const user = userEvent.setup();

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await user.click(screen.getByTestId('set-dark'));

      expect(localStorage.getItem(STORAGE_KEY)).toBe('dark');
    });

    it('should save light theme to localStorage', async () => {
      const user = userEvent.setup();

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      await user.click(screen.getByTestId('set-light'));

      expect(localStorage.getItem(STORAGE_KEY)).toBe('light');
    });

    it('should save system theme to localStorage', async () => {
      const user = userEvent.setup();

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      // First set to dark
      await user.click(screen.getByTestId('set-dark'));
      expect(localStorage.getItem(STORAGE_KEY)).toBe('dark');

      // Then back to system
      await user.click(screen.getByTestId('set-system'));
      expect(localStorage.getItem(STORAGE_KEY)).toBe('system');
    });

    it('should restore theme from localStorage on mount', () => {
      // Pre-populate localStorage
      localStorage.setItem(STORAGE_KEY, 'dark');

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark');
    });

    it('should restore light theme from localStorage', () => {
      localStorage.setItem(STORAGE_KEY, 'light');

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('theme')).toHaveTextContent('light');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light');
    });

    it('should default to system for invalid localStorage value', () => {
      localStorage.setItem(STORAGE_KEY, 'invalid-theme-value');

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('theme')).toHaveTextContent('system');
    });
  });

  // ---------------------------------------------------------------------------
  // resolvedTheme Calculation Tests
  // ---------------------------------------------------------------------------
  describe('resolvedTheme calculation', () => {
    it('should resolve to light when theme is light regardless of system preference', () => {
      mockMatchMedia(true); // System prefers dark
      localStorage.setItem(STORAGE_KEY, 'light');

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('theme')).toHaveTextContent('light');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light');
    });

    it('should resolve to dark when theme is dark regardless of system preference', () => {
      mockMatchMedia(false); // System prefers light
      localStorage.setItem(STORAGE_KEY, 'dark');

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('theme')).toHaveTextContent('dark');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark');
    });

    it('should resolve system theme to light when system prefers light', () => {
      mockMatchMedia(false);
      localStorage.setItem(STORAGE_KEY, 'system');

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('theme')).toHaveTextContent('system');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light');
    });

    it('should resolve system theme to dark when system prefers dark', () => {
      mockMatchMedia(true);
      localStorage.setItem(STORAGE_KEY, 'system');

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('theme')).toHaveTextContent('system');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark');
    });
  });

  // ---------------------------------------------------------------------------
  // DOM Class Application Tests
  // ---------------------------------------------------------------------------
  describe('DOM class application', () => {
    it('should apply light class to document when resolved theme is light', () => {
      mockMatchMedia(false);

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(document.documentElement.classList.contains('light')).toBe(true);
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });

    it('should apply dark class to document when resolved theme is dark', () => {
      mockMatchMedia(true);

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(document.documentElement.classList.contains('dark')).toBe(true);
      expect(document.documentElement.classList.contains('light')).toBe(false);
    });

    it('should switch DOM class when theme changes', async () => {
      const user = userEvent.setup();
      mockMatchMedia(false);

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      // Initially light
      expect(document.documentElement.classList.contains('light')).toBe(true);

      // Change to dark
      await user.click(screen.getByTestId('set-dark'));

      await waitFor(() => {
        expect(document.documentElement.classList.contains('dark')).toBe(true);
        expect(document.documentElement.classList.contains('light')).toBe(false);
      });
    });
  });

  // ---------------------------------------------------------------------------
  // useTheme Hook Error Tests
  // ---------------------------------------------------------------------------
  describe('useTheme hook', () => {
    it('should throw error when used outside ThemeProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestComponent />);
      }).toThrow('useTheme must be used within a ThemeProvider');

      consoleSpy.mockRestore();
    });
  });

  // ---------------------------------------------------------------------------
  // System Theme Change Listener Tests
  // ---------------------------------------------------------------------------
  describe('system theme change listener', () => {
    it('should update resolvedTheme when system preference changes and theme is system', async () => {
      const { simulateSystemThemeChange } = mockMatchMedia(false); // Start with light

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      expect(screen.getByTestId('theme')).toHaveTextContent('system');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light');

      // Simulate system changing to dark
      simulateSystemThemeChange(true);

      await waitFor(() => {
        expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark');
      });

      // Theme should still be system
      expect(screen.getByTestId('theme')).toHaveTextContent('system');
    });

    it('should not update resolvedTheme when system changes but theme is explicitly set', async () => {
      const user = userEvent.setup();
      const { simulateSystemThemeChange } = mockMatchMedia(false); // Start with light

      render(
        <ThemeProvider>
          <TestComponent />
        </ThemeProvider>
      );

      // Set explicit light theme
      await user.click(screen.getByTestId('set-light'));
      expect(screen.getByTestId('theme')).toHaveTextContent('light');
      expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light');

      // Simulate system changing to dark
      simulateSystemThemeChange(true);

      // resolvedTheme should remain light because theme is explicitly set
      await waitFor(() => {
        expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light');
      });
    });
  });
});