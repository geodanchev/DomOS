import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../test/test-utils'
import Login from './Login'
import { mockLoginResponse } from '../test/mocks/data'

// Mock react-router-dom navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock the API module
vi.mock('../services/api', () => ({
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
  },
}))

import { authApi } from '../services/api'

describe('Login Page', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Rendering', () => {
    it('renders login form correctly', () => {
      render(<Login />)

      // Check for title
      expect(screen.getByText('🏠 DomOS')).toBeInTheDocument()
      expect(screen.getByText('Дигитален касиер')).toBeInTheDocument()

      // Check for form elements
      expect(screen.getByLabelText(/потребителско име/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/парола/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /вход/i })).toBeInTheDocument()

      // Check for demo credentials
      expect(screen.getByText(/демо достъп/i)).toBeInTheDocument()
      expect(screen.getByText(/cecka \/ 1234/i)).toBeInTheDocument()
      expect(screen.getByText(/admin \/ admin123/i)).toBeInTheDocument()
    })

    it('username input has autofocus', () => {
      render(<Login />)
      const usernameInput = screen.getByLabelText(/потребителско име/i)
      expect(usernameInput).toHaveFocus()
    })
  })

  describe('Form Validation', () => {
    it('requires username and password fields', () => {
      render(<Login />)
      
      const usernameInput = screen.getByLabelText(/потребителско име/i)
      const passwordInput = screen.getByLabelText(/парола/i)

      expect(usernameInput).toBeRequired()
      expect(passwordInput).toBeRequired()
    })

    it('allows input in both fields', async () => {
      const user = userEvent.setup()
      render(<Login />)

      const usernameInput = screen.getByLabelText(/потребителско име/i)
      const passwordInput = screen.getByLabelText(/парола/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'testpass')

      expect(usernameInput).toHaveValue('testuser')
      expect(passwordInput).toHaveValue('testpass')
    })
  })

  describe('Login Submission', () => {
    it('calls login with correct credentials on form submit', async () => {
      const user = userEvent.setup()
      vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse)

      render(<Login />)

      await user.type(screen.getByLabelText(/потребителско име/i), 'admin')
      await user.type(screen.getByLabelText(/парола/i), 'admin123')
      await user.click(screen.getByRole('button', { name: /вход/i }))

      await waitFor(() => {
        expect(authApi.login).toHaveBeenCalledWith('admin', 'admin123')
      })
    })

    it('navigates to home page on successful login', async () => {
      const user = userEvent.setup()
      vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse)

      render(<Login />)

      await user.type(screen.getByLabelText(/потребителско име/i), 'admin')
      await user.type(screen.getByLabelText(/парола/i), 'admin123')
      await user.click(screen.getByRole('button', { name: /вход/i }))

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/')
      })
    })

    it('shows loading state during login', async () => {
      const user = userEvent.setup()
      // Create a promise that we can control
      let resolveLogin: (value: typeof mockLoginResponse) => void
      vi.mocked(authApi.login).mockImplementation(
        () => new Promise((resolve) => { resolveLogin = resolve })
      )

      render(<Login />)

      await user.type(screen.getByLabelText(/потребителско име/i), 'admin')
      await user.type(screen.getByLabelText(/парола/i), 'admin123')
      await user.click(screen.getByRole('button', { name: /вход/i }))

      // Button should show loading state
      await waitFor(() => {
        expect(screen.getByText(/влизане/i)).toBeInTheDocument()
      })

      // Resolve the login
      resolveLogin!(mockLoginResponse)
    })

    it('disables button during login', async () => {
      const user = userEvent.setup()
      let resolveLogin: (value: typeof mockLoginResponse) => void
      vi.mocked(authApi.login).mockImplementation(
        () => new Promise((resolve) => { resolveLogin = resolve })
      )

      render(<Login />)

      await user.type(screen.getByLabelText(/потребителско име/i), 'admin')
      await user.type(screen.getByLabelText(/парола/i), 'admin123')
      await user.click(screen.getByRole('button', { name: /вход/i }))

      await waitFor(() => {
        const button = screen.getByRole('button')
        expect(button).toBeDisabled()
      })

      resolveLogin!(mockLoginResponse)
    })
  })

  describe('Error Handling', () => {
    it('displays error message on failed login', async () => {
      const user = userEvent.setup()
      vi.mocked(authApi.login).mockRejectedValue({
        response: { data: { detail: 'Невалидно потребителско име или парола' } },
      })

      render(<Login />)

      await user.type(screen.getByLabelText(/потребителско име/i), 'wrong')
      await user.type(screen.getByLabelText(/парола/i), 'wrong')
      await user.click(screen.getByRole('button', { name: /вход/i }))

      await waitFor(() => {
        expect(screen.getByText(/невалидно потребителско име или парола/i)).toBeInTheDocument()
      })
    })

    it('displays generic error message when no detail provided', async () => {
      const user = userEvent.setup()
      vi.mocked(authApi.login).mockRejectedValue(new Error('Network error'))

      render(<Login />)

      await user.type(screen.getByLabelText(/потребителско име/i), 'admin')
      await user.type(screen.getByLabelText(/парола/i), 'admin123')
      await user.click(screen.getByRole('button', { name: /вход/i }))

      await waitFor(() => {
        expect(screen.getByText(/грешка при вход/i)).toBeInTheDocument()
      })
    })

    it('clears error message when retrying login', async () => {
      const user = userEvent.setup()
      vi.mocked(authApi.login)
        .mockRejectedValueOnce({
          response: { data: { detail: 'Грешка' } },
        })
        .mockResolvedValueOnce(mockLoginResponse)

      render(<Login />)

      // First attempt - fails
      await user.type(screen.getByLabelText(/потребителско име/i), 'wrong')
      await user.type(screen.getByLabelText(/парола/i), 'wrong')
      await user.click(screen.getByRole('button', { name: /вход/i }))

      await waitFor(() => {
        expect(screen.getByText('Грешка')).toBeInTheDocument()
      })

      // Second attempt - should clear error first
      await user.clear(screen.getByLabelText(/потребителско име/i))
      await user.clear(screen.getByLabelText(/парола/i))
      await user.type(screen.getByLabelText(/потребителско име/i), 'admin')
      await user.type(screen.getByLabelText(/парола/i), 'admin123')
      await user.click(screen.getByRole('button', { name: /вход/i }))

      // Error should be cleared after clicking button
      await waitFor(() => {
        expect(screen.queryByText('Грешка')).not.toBeInTheDocument()
      })
    })
  })
})
