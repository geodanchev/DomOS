import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from './AuthContext'
import { mockLoginResponse, mockUser } from '../test/mocks/data'

// Mock the API module
vi.mock('../services/api', () => ({
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
  },
}))

import { authApi } from '../services/api'

describe('AuthContext', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('useAuth hook', () => {
    it('throws error when used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      expect(() => {
        renderHook(() => useAuth())
      }).toThrow('useAuth must be used within an AuthProvider')
      
      consoleSpy.mockRestore()
    })

    it('returns initial unauthenticated state', async () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.user).toBeNull()
      expect(result.current.token).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
    })

    it('loads existing session from localStorage', async () => {
      // Pre-populate localStorage
      localStorage.setItem('token', 'existing-token')
      localStorage.setItem('user', JSON.stringify(mockUser))

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.token).toBe('existing-token')
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
    })
  })

  describe('login', () => {
    it('successfully logs in user', async () => {
      vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse)

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await act(async () => {
        await result.current.login('admin', 'admin123')
      })

      expect(authApi.login).toHaveBeenCalledWith('admin', 'admin123')
      expect(result.current.token).toBe(mockLoginResponse.access_token)
      expect(result.current.user).toEqual(mockLoginResponse.user)
      expect(result.current.isAuthenticated).toBe(true)
      
      // Verify localStorage was updated
      expect(localStorage.getItem('token')).toBe(mockLoginResponse.access_token)
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockLoginResponse.user))
    })

    it('throws error on failed login', async () => {
      const error = new Error('Invalid credentials')
      vi.mocked(authApi.login).mockRejectedValue(error)

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await expect(
        act(async () => {
          await result.current.login('wrong', 'credentials')
        })
      ).rejects.toThrow('Invalid credentials')

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
    })
  })

  describe('logout', () => {
    it('clears user session', async () => {
      // Start with authenticated state
      localStorage.setItem('token', 'existing-token')
      localStorage.setItem('user', JSON.stringify(mockUser))

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true)
      })

      act(() => {
        result.current.logout()
      })

      expect(result.current.user).toBeNull()
      expect(result.current.token).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
      expect(localStorage.getItem('token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
    })
  })
})
