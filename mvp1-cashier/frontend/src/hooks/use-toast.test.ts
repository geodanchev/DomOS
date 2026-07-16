import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useToast, toast, reducer } from './use-toast'

// Mock timers for testing auto-dismiss
vi.useFakeTimers()

describe('use-toast', () => {
  beforeEach(() => {
    vi.clearAllTimers()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  describe('useToast hook', () => {
    it('should return initial empty toasts array', () => {
      const { result } = renderHook(() => useToast())
      
      // Initial state may have toasts from previous tests due to global state
      expect(result.current.toasts).toBeDefined()
      expect(Array.isArray(result.current.toasts)).toBe(true)
    })

    it('should return toast function', () => {
      const { result } = renderHook(() => useToast())
      
      expect(result.current.toast).toBeDefined()
      expect(typeof result.current.toast).toBe('function')
    })

    it('should return dismiss function', () => {
      const { result } = renderHook(() => useToast())
      
      expect(result.current.dismiss).toBeDefined()
      expect(typeof result.current.dismiss).toBe('function')
    })

    it('should add toast when toast() is called', () => {
      const { result } = renderHook(() => useToast())
      const initialLength = result.current.toasts.length

      act(() => {
        result.current.toast({
          title: 'Test Toast',
          description: 'This is a test description'
        })
      })

      expect(result.current.toasts.length).toBe(initialLength + 1)
      expect(result.current.toasts[0].title).toBe('Test Toast')
      expect(result.current.toasts[0].description).toBe('This is a test description')
    })

    it('should add toast with open: true', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.toast({
          title: 'Open Toast'
        })
      })

      expect(result.current.toasts[0].open).toBe(true)
    })

    it('should generate unique id for each toast', () => {
      const { result } = renderHook(() => useToast())

      let id1: string
      let id2: string

      act(() => {
        const toast1 = result.current.toast({ title: 'Toast 1' })
        id1 = toast1.id
      })

      act(() => {
        const toast2 = result.current.toast({ title: 'Toast 2' })
        id2 = toast2.id
      })

      expect(id1!).not.toBe(id2!)
    })

    it('should dismiss specific toast by id', () => {
      const { result } = renderHook(() => useToast())
      let toastId: string

      act(() => {
        const newToast = result.current.toast({ title: 'Dismissable Toast' })
        toastId = newToast.id
      })

      // Verify toast is open
      const toastBefore = result.current.toasts.find(t => t.id === toastId!)
      expect(toastBefore?.open).toBe(true)

      act(() => {
        result.current.dismiss(toastId!)
      })

      // After dismiss, the toast should have open: false
      const toastAfter = result.current.toasts.find(t => t.id === toastId!)
      expect(toastAfter?.open).toBe(false)
    })

    it('should dismiss all toasts when no id provided', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.toast({ title: 'Toast 1' })
      })

      act(() => {
        result.current.dismiss()
      })

      // All toasts should have open: false
      result.current.toasts.forEach(t => {
        expect(t.open).toBe(false)
      })
    })

    it('should update toast using returned update function', () => {
      const { result } = renderHook(() => useToast())
      let updateFn: (props: any) => void
      let toastId: string

      act(() => {
        const newToast = result.current.toast({ 
          title: 'Original Title',
          description: 'Original Description'
        })
        updateFn = newToast.update
        toastId = newToast.id
      })

      act(() => {
        updateFn({ 
          id: toastId!,
          title: 'Updated Title',
          description: 'Updated Description'
        })
      })

      const updatedToast = result.current.toasts.find(t => t.id === toastId!)
      expect(updatedToast?.title).toBe('Updated Title')
      expect(updatedToast?.description).toBe('Updated Description')
    })

    it('should dismiss toast using returned dismiss function', () => {
      const { result } = renderHook(() => useToast())
      let dismissFn: () => void
      let toastId: string

      act(() => {
        const newToast = result.current.toast({ title: 'To be dismissed' })
        dismissFn = newToast.dismiss
        toastId = newToast.id
      })

      act(() => {
        dismissFn()
      })

      const toast = result.current.toasts.find(t => t.id === toastId!)
      expect(toast?.open).toBe(false)
    })

    it('should limit toasts to TOAST_LIMIT (1)', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.toast({ title: 'Toast 1' })
      })

      act(() => {
        result.current.toast({ title: 'Toast 2' })
      })

      // TOAST_LIMIT is 1, so only the newest toast should be visible
      // The toasts array should have at most 1 element
      expect(result.current.toasts.filter(t => t.open).length).toBeLessThanOrEqual(1)
    })
  })

  describe('toast() standalone function', () => {
    it('should return id, dismiss, and update functions', () => {
      let result: { id: string; dismiss: () => void; update: (props: any) => void }

      act(() => {
        result = toast({ title: 'Standalone Toast' })
      })

      expect(result!.id).toBeDefined()
      expect(typeof result!.dismiss).toBe('function')
      expect(typeof result!.update).toBe('function')
    })
  })

  describe('reducer', () => {
    const initialState = { toasts: [] }

    it('should handle ADD_TOAST action', () => {
      const newToast = {
        id: '1',
        title: 'New Toast',
        open: true
      }

      const result = reducer(initialState, {
        type: 'ADD_TOAST',
        toast: newToast as any
      })

      expect(result.toasts).toHaveLength(1)
      expect(result.toasts[0].id).toBe('1')
      expect(result.toasts[0].title).toBe('New Toast')
    })

    it('should handle UPDATE_TOAST action', () => {
      const state = {
        toasts: [{ id: '1', title: 'Original', open: true } as any]
      }

      const result = reducer(state, {
        type: 'UPDATE_TOAST',
        toast: { id: '1', title: 'Updated' }
      })

      expect(result.toasts[0].title).toBe('Updated')
      expect(result.toasts[0].open).toBe(true)
    })

    it('should handle DISMISS_TOAST action with specific id', () => {
      const state = {
        toasts: [
          { id: '1', title: 'Toast 1', open: true } as any,
          { id: '2', title: 'Toast 2', open: true } as any
        ]
      }

      const result = reducer(state, {
        type: 'DISMISS_TOAST',
        toastId: '1'
      })

      expect(result.toasts.find(t => t.id === '1')?.open).toBe(false)
      expect(result.toasts.find(t => t.id === '2')?.open).toBe(true)
    })

    it('should handle DISMISS_TOAST action without id (dismiss all)', () => {
      const state = {
        toasts: [
          { id: '1', title: 'Toast 1', open: true } as any,
          { id: '2', title: 'Toast 2', open: true } as any
        ]
      }

      const result = reducer(state, {
        type: 'DISMISS_TOAST'
      })

      expect(result.toasts.every(t => t.open === false)).toBe(true)
    })

    it('should handle REMOVE_TOAST action with specific id', () => {
      const state = {
        toasts: [
          { id: '1', title: 'Toast 1', open: true } as any,
          { id: '2', title: 'Toast 2', open: true } as any
        ]
      }

      const result = reducer(state, {
        type: 'REMOVE_TOAST',
        toastId: '1'
      })

      expect(result.toasts).toHaveLength(1)
      expect(result.toasts[0].id).toBe('2')
    })

    it('should handle REMOVE_TOAST action without id (remove all)', () => {
      const state = {
        toasts: [
          { id: '1', title: 'Toast 1', open: true } as any,
          { id: '2', title: 'Toast 2', open: true } as any
        ]
      }

      const result = reducer(state, {
        type: 'REMOVE_TOAST'
      })

      expect(result.toasts).toHaveLength(0)
    })

    it('should limit toasts to TOAST_LIMIT on ADD_TOAST', () => {
      const state = {
        toasts: [{ id: '1', title: 'Existing', open: true } as any]
      }

      const result = reducer(state, {
        type: 'ADD_TOAST',
        toast: { id: '2', title: 'New', open: true } as any
      })

      // TOAST_LIMIT is 1, new toast should be first, old one removed
      expect(result.toasts).toHaveLength(1)
      expect(result.toasts[0].id).toBe('2')
    })
  })

  describe('toast variants', () => {
    it('should support default variant', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.toast({
          title: 'Default Toast',
          variant: 'default'
        })
      })

      expect(result.current.toasts[0].variant).toBe('default')
    })

    it('should support destructive variant', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.toast({
          title: 'Error Toast',
          variant: 'destructive'
        })
      })

      expect(result.current.toasts[0].variant).toBe('destructive')
    })

    it('should handle toast with action element', () => {
      const { result } = renderHook(() => useToast())
      const mockAction = { type: 'mock' } as any

      act(() => {
        result.current.toast({
          title: 'Toast with Action',
          action: mockAction
        })
      })

      expect(result.current.toasts[0].action).toBe(mockAction)
    })
  })

  describe('onOpenChange callback', () => {
    it('should call dismiss when onOpenChange receives false', () => {
      const { result } = renderHook(() => useToast())
      let toastId: string

      act(() => {
        const newToast = result.current.toast({ title: 'Closeable Toast' })
        toastId = newToast.id
      })

      const addedToast = result.current.toasts.find(t => t.id === toastId!)
      expect(addedToast?.onOpenChange).toBeDefined()

      // Simulate closing via onOpenChange
      act(() => {
        addedToast?.onOpenChange?.(false)
      })

      const closedToast = result.current.toasts.find(t => t.id === toastId!)
      expect(closedToast?.open).toBe(false)
    })
  })

  describe('multiple hook instances', () => {
    it('should share state between multiple useToast instances', () => {
      const { result: result1 } = renderHook(() => useToast())
      const { result: result2 } = renderHook(() => useToast())

      act(() => {
        result1.current.toast({ title: 'Shared Toast' })
      })

      // Both instances should see the same toast
      expect(result1.current.toasts[0].title).toBe('Shared Toast')
      expect(result2.current.toasts[0].title).toBe('Shared Toast')
    })
  })
})
