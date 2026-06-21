import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../test/test-utils'
import Dashboard from './Dashboard'
import { mockDashboard, mockFundBalance, mockUser } from '../test/mocks/data'

// Mock the API module
vi.mock('../services/api', () => ({
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
  },
  dashboardApi: {
    getDashboard: vi.fn(),
    getFundBalance: vi.fn(),
  },
  paymentsApi: {
    create: vi.fn(),
  },
}))

import { dashboardApi } from '../services/api'

describe('Dashboard Page', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('user', JSON.stringify(mockUser))
    vi.clearAllMocks()
    
    // Default mock implementations
    vi.mocked(dashboardApi.getDashboard).mockResolvedValue(mockDashboard)
    vi.mocked(dashboardApi.getFundBalance).mockResolvedValue(mockFundBalance)
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Loading State', () => {
    it('shows loading spinner initially', () => {
      // Make API calls hang
      vi.mocked(dashboardApi.getDashboard).mockImplementation(
        () => new Promise(() => {})
      )
      vi.mocked(dashboardApi.getFundBalance).mockImplementation(
        () => new Promise(() => {})
      )

      render(<Dashboard />)

      // Check for loading spinner (the animate-spin class)
      expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('displays error message when API fails', async () => {
      vi.mocked(dashboardApi.getDashboard).mockRejectedValue(new Error('API Error'))

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/грешка при зареждане/i)).toBeInTheDocument()
      })
    })

    it('shows retry button on error', async () => {
      vi.mocked(dashboardApi.getDashboard).mockRejectedValue(new Error('API Error'))

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/опитай пак/i)).toBeInTheDocument()
      })
    })

    it('retries loading data when retry button clicked', async () => {
      const user = userEvent.setup()
      vi.mocked(dashboardApi.getDashboard)
        .mockRejectedValueOnce(new Error('API Error'))
        .mockResolvedValueOnce(mockDashboard)

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/грешка при зареждане/i)).toBeInTheDocument()
      })

      await user.click(screen.getByText(/опитай пак/i))

      await waitFor(() => {
        expect(dashboardApi.getDashboard).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Data Display', () => {
    it('renders dashboard header with current month', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/табло/i)).toBeInTheDocument()
        // January 2024 in Bulgarian
        expect(screen.getByText(/януари 2024/i)).toBeInTheDocument()
      })
    })

    it('displays fund balance card', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/баланс на фонда/i)).toBeInTheDocument()
        expect(screen.getByText('1300.00 лв')).toBeInTheDocument()
      })
    })

    it('displays collected amount card', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/събрано този месец/i)).toBeInTheDocument()
        expect(screen.getByText('70.00 лв')).toBeInTheDocument()
      })
    })

    it('displays remaining amount card', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/остават за събиране/i)).toBeInTheDocument()
        expect(screen.getByText('80.00 лв')).toBeInTheDocument()
      })
    })

    it('displays collection rate card', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/събираемост/i)).toBeInTheDocument()
        expect(screen.getByText('46.67%')).toBeInTheDocument()
      })
    })

    it('displays quick stats badges', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        // Use getAllBy since text appears in multiple places, check that we have at least one
        const paidBadges = screen.getAllByText(/✓ платили/i)
        const partialBadges = screen.getAllByText(/◐ частично/i)
        const unpaidBadges = screen.getAllByText(/✗ неплатили/i)
        expect(paidBadges.length).toBeGreaterThan(0)
        expect(partialBadges.length).toBeGreaterThan(0)
        expect(unpaidBadges.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Apartments Table', () => {
    it('renders apartments table header', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/🏠 апартаменти/i)).toBeInTheDocument()
        // Use getByRole to target table headers specifically
        const table = screen.getByRole('table')
        expect(within(table).getByText('Ап.')).toBeInTheDocument()
        expect(within(table).getByText('Собственик')).toBeInTheDocument()
        expect(within(table).getByText('Дължи')).toBeInTheDocument()
        expect(within(table).getByText('Статус')).toBeInTheDocument()
        expect(within(table).getByText('Действие')).toBeInTheDocument()
      })
    })

    it('renders all apartments', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Иван Петров')).toBeInTheDocument()
        expect(screen.getByText('Мария Иванова')).toBeInTheDocument()
        expect(screen.getByText('Георги Димитров')).toBeInTheDocument()
      })
    })

    it('displays correct status badges in table', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        // Target the status badges with their specific class
        const paidBadge = document.querySelector('.status-paid')
        const partialBadge = document.querySelector('.status-partial')
        const unpaidBadge = document.querySelector('.status-unpaid')
        expect(paidBadge).toBeInTheDocument()
        expect(partialBadge).toBeInTheDocument()
        expect(unpaidBadge).toBeInTheDocument()
      })
    })

    it('shows pay button only for unpaid apartments', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        const payButtons = screen.getAllByText(/💵 плати/i)
        // Only 2 apartments are not fully paid (partial + unpaid)
        expect(payButtons).toHaveLength(2)
      })
    })

    it('shows amounts with correct formatting', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        // Check for unique amounts in the table (45.00 and 55.00 are unique)
        expect(screen.getByText('45.00 лв')).toBeInTheDocument()
        expect(screen.getByText('55.00 лв')).toBeInTheDocument()
        // 50.00 appears twice (due and paid for first apartment), so use getAllBy
        const fiftyAmounts = screen.getAllByText('50.00 лв')
        expect(fiftyAmounts.length).toBeGreaterThanOrEqual(1)
      })
    })
  })

  describe('Refresh Button', () => {
    it('renders refresh button', async () => {
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/🔄 опресни/i)).toBeInTheDocument()
      })
    })

    it('refreshes data when clicked', async () => {
      const user = userEvent.setup()
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/🔄 опресни/i)).toBeInTheDocument()
      })

      await user.click(screen.getByText(/🔄 опресни/i))

      await waitFor(() => {
        // Initial call + refresh call
        expect(dashboardApi.getDashboard).toHaveBeenCalledTimes(2)
        expect(dashboardApi.getFundBalance).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Payment Modal', () => {
    it('opens payment modal when pay button clicked', async () => {
      const user = userEvent.setup()
      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getAllByText(/💵 плати/i)).toHaveLength(2)
      })

      // Click the first pay button (for partial payment apartment)
      const payButtons = screen.getAllByText(/💵 плати/i)
      await user.click(payButtons[0])

      await waitFor(() => {
        // Check for modal title - actual title is "Ново плащане"
        expect(screen.getByText(/💵 ново плащане/i)).toBeInTheDocument()
      })
    })
  })
})
