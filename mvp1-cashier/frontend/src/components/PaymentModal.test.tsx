import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../test/test-utils'
import PaymentModal from './PaymentModal'
import type { ApartmentStatus } from '../types'
import { mockUser } from '../test/mocks/data'

// Mock the API module
vi.mock('../services/api', () => ({
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
  },
  paymentsApi: {
    create: vi.fn(),
  },
}))

import { paymentsApi } from '../services/api'

const mockApartment: ApartmentStatus = {
  apartment_id: 2,
  apartment_number: '2',
  owner_name: 'Мария Иванова',
  amount_due: 45,
  amount_paid: 20,
  status: 'partial',
  status_display: 'Частично',
}

const defaultProps = {
  apartment: mockApartment,
  month: '2024-01',
  onClose: vi.fn(),
  onSuccess: vi.fn(),
}

describe('PaymentModal Component', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('user', JSON.stringify(mockUser))
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Rendering', () => {
    it('renders modal with correct title', () => {
      render(<PaymentModal {...defaultProps} />)

      expect(screen.getByText(/💵 ново плащане/i)).toBeInTheDocument()
    })

    it('displays apartment information', () => {
      render(<PaymentModal {...defaultProps} />)

      expect(screen.getByText('2')).toBeInTheDocument() // apartment number
      expect(screen.getByText('Мария Иванова')).toBeInTheDocument()
      expect(screen.getByText('45.00 лв')).toBeInTheDocument() // amount due
      expect(screen.getByText('20.00 лв')).toBeInTheDocument() // amount paid
      expect(screen.getByText('25.00 лв')).toBeInTheDocument() // remaining
    })

    it('displays quick amount buttons', () => {
      render(<PaymentModal {...defaultProps} />)

      expect(screen.getByText('Цяла сума')).toBeInTheDocument()
      expect(screen.getByText('10 лв')).toBeInTheDocument()
      expect(screen.getByText('20 лв')).toBeInTheDocument()
      expect(screen.getByText('50 лв')).toBeInTheDocument()
    })

    it('displays payment method buttons', () => {
      render(<PaymentModal {...defaultProps} />)

      expect(screen.getByText('💵 В брой')).toBeInTheDocument()
      expect(screen.getByText('🏦 Банка')).toBeInTheDocument()
      expect(screen.getByText('💳 Карта')).toBeInTheDocument()
    })

    it('displays action buttons', () => {
      render(<PaymentModal {...defaultProps} />)

      expect(screen.getByText('Отказ')).toBeInTheDocument()
      expect(screen.getByText(/✓ запиши плащане/i)).toBeInTheDocument()
    })

    it('has close button', () => {
      render(<PaymentModal {...defaultProps} />)

      expect(screen.getByText('×')).toBeInTheDocument()
    })

    it('pre-fills amount with remaining balance', () => {
      render(<PaymentModal {...defaultProps} />)

      const amountInput = screen.getByDisplayValue('25.00')
      expect(amountInput).toBeInTheDocument()
    })

    it('defaults to cash payment method', () => {
      render(<PaymentModal {...defaultProps} />)

      const cashButton = screen.getByText('💵 В брой')
      // Check that cash button has the selected styling
      expect(cashButton.closest('button')).toHaveClass('border-primary-500')
    })
  })

  describe('User Interactions', () => {
    it('updates amount when quick amount button clicked', async () => {
      const user = userEvent.setup()
      render(<PaymentModal {...defaultProps} />)

      await user.click(screen.getByText('10 лв'))

      const amountInput = screen.getByRole('spinbutton')
      expect(amountInput).toHaveValue(10)
    })

    it('updates amount when "Цяла сума" button clicked', async () => {
      const user = userEvent.setup()
      render(<PaymentModal {...defaultProps} />)

      // First change to something else
      await user.click(screen.getByText('10 лв'))
      expect(screen.getByRole('spinbutton')).toHaveValue(10)

      // Then click "Цяла сума"
      await user.click(screen.getByText('Цяла сума'))
      expect(screen.getByRole('spinbutton')).toHaveValue(25)
    })

    it('allows manual amount entry', async () => {
      const user = userEvent.setup()
      render(<PaymentModal {...defaultProps} />)

      const amountInput = screen.getByRole('spinbutton')
      await user.clear(amountInput)
      await user.type(amountInput, '15.50')

      expect(amountInput).toHaveValue(15.5)
    })

    it('changes payment method when clicked', async () => {
      const user = userEvent.setup()
      render(<PaymentModal {...defaultProps} />)

      const bankButton = screen.getByText('🏦 Банка')
      await user.click(bankButton)

      // Bank button should now have selected styling
      expect(bankButton.closest('button')).toHaveClass('border-primary-500')
      
      // Cash should not have selected styling
      const cashButton = screen.getByText('💵 В брой')
      expect(cashButton.closest('button')).not.toHaveClass('border-primary-500')
    })

    it('allows entering notes', async () => {
      const user = userEvent.setup()
      render(<PaymentModal {...defaultProps} />)

      const notesInput = screen.getByPlaceholderText(/платено от съпруга/i)
      await user.type(notesInput, 'Тест бележка')

      expect(notesInput).toHaveValue('Тест бележка')
    })

    it('calls onClose when close button clicked', async () => {
      const user = userEvent.setup()
      render(<PaymentModal {...defaultProps} />)

      await user.click(screen.getByText('×'))

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
    })

    it('calls onClose when cancel button clicked', async () => {
      const user = userEvent.setup()
      render(<PaymentModal {...defaultProps} />)

      await user.click(screen.getByText('Отказ'))

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('Form Submission', () => {
    it('submits payment with correct data', async () => {
      const user = userEvent.setup()
      vi.mocked(paymentsApi.create).mockResolvedValue({
        id: 999,
        apartment_id: 2,
        amount: 25,
        month: '2024-01',
        payment_date: '2024-01-20',
        payment_method: 'cash',
        collected_by_id: 1,
        notes: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })

      render(<PaymentModal {...defaultProps} />)

      await user.click(screen.getByText(/✓ запиши плащане/i))

      await waitFor(() => {
        expect(paymentsApi.create).toHaveBeenCalledWith({
          apartment_id: 2,
          amount: 25,
          month: '2024-01',
          payment_method: 'cash',
          notes: undefined,
        })
      })
    })

    it('calls onSuccess after successful submission', async () => {
      const user = userEvent.setup()
      vi.mocked(paymentsApi.create).mockResolvedValue({
        id: 999,
        apartment_id: 2,
        amount: 25,
        month: '2024-01',
        payment_date: '2024-01-20',
        payment_method: 'cash',
        collected_by_id: 1,
        notes: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })

      render(<PaymentModal {...defaultProps} />)

      await user.click(screen.getByText(/✓ запиши плащане/i))

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalledTimes(1)
      })
    })

    it('shows loading state during submission', async () => {
      const user = userEvent.setup()
      let resolveCreate: (value: any) => void
      vi.mocked(paymentsApi.create).mockImplementation(
        () => new Promise((resolve) => { resolveCreate = resolve })
      )

      render(<PaymentModal {...defaultProps} />)

      await user.click(screen.getByText(/✓ запиши плащане/i))

      await waitFor(() => {
        expect(screen.getByText(/записване/i)).toBeInTheDocument()
      })

      // Resolve to clean up
      resolveCreate!({})
    })

    it('disables buttons during submission', async () => {
      const user = userEvent.setup()
      let resolveCreate: (value: any) => void
      vi.mocked(paymentsApi.create).mockImplementation(
        () => new Promise((resolve) => { resolveCreate = resolve })
      )

      render(<PaymentModal {...defaultProps} />)

      await user.click(screen.getByText(/✓ запиши плащане/i))

      await waitFor(() => {
        expect(screen.getByText('Отказ')).toBeDisabled()
      })

      // Resolve to clean up
      resolveCreate!({})
    })

    it('includes notes when provided', async () => {
      const user = userEvent.setup()
      vi.mocked(paymentsApi.create).mockResolvedValue({
        id: 999,
        apartment_id: 2,
        amount: 25,
        month: '2024-01',
        payment_date: '2024-01-20',
        payment_method: 'cash',
        collected_by_id: 1,
        notes: 'Тест бележка',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })

      render(<PaymentModal {...defaultProps} />)

      const notesInput = screen.getByPlaceholderText(/платено от съпруга/i)
      await user.type(notesInput, 'Тест бележка')
      await user.click(screen.getByText(/✓ запиши плащане/i))

      await waitFor(() => {
        expect(paymentsApi.create).toHaveBeenCalledWith(
          expect.objectContaining({
            notes: 'Тест бележка',
          })
        )
      })
    })

    it('submits with selected payment method', async () => {
      const user = userEvent.setup()
      vi.mocked(paymentsApi.create).mockResolvedValue({
        id: 999,
        apartment_id: 2,
        amount: 25,
        month: '2024-01',
        payment_date: '2024-01-20',
        payment_method: 'card',
        collected_by_id: 1,
        notes: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })

      render(<PaymentModal {...defaultProps} />)

      await user.click(screen.getByText('💳 Карта'))
      await user.click(screen.getByText(/✓ запиши плащане/i))

      await waitFor(() => {
        expect(paymentsApi.create).toHaveBeenCalledWith(
          expect.objectContaining({
            payment_method: 'card',
          })
        )
      })
    })
  })

  describe('Error Handling', () => {
    it('displays error message on submission failure', async () => {
      const user = userEvent.setup()
      vi.mocked(paymentsApi.create).mockRejectedValue({
        response: { data: { detail: 'Грешка при запис' } },
      })

      render(<PaymentModal {...defaultProps} />)

      await user.click(screen.getByText(/✓ запиши плащане/i))

      await waitFor(() => {
        expect(screen.getByText('Грешка при запис')).toBeInTheDocument()
      })
    })

    it('displays generic error message when no detail provided', async () => {
      const user = userEvent.setup()
      vi.mocked(paymentsApi.create).mockRejectedValue(new Error('Network error'))

      render(<PaymentModal {...defaultProps} />)

      await user.click(screen.getByText(/✓ запиши плащане/i))

      await waitFor(() => {
        expect(screen.getByText(/грешка при запис на плащането/i)).toBeInTheDocument()
      })
    })

    it('does not call onSuccess on error', async () => {
      const user = userEvent.setup()
      vi.mocked(paymentsApi.create).mockRejectedValue({
        response: { data: { detail: 'Грешка' } },
      })

      render(<PaymentModal {...defaultProps} />)

      await user.click(screen.getByText(/✓ запиши плащане/i))

      await waitFor(() => {
        expect(screen.getByText('Грешка')).toBeInTheDocument()
      })

      expect(defaultProps.onSuccess).not.toHaveBeenCalled()
    })
  })
})