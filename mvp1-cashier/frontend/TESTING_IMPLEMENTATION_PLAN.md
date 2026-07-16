# Frontend Testing Implementation Plan

## Обзор

Този план описва стъпките за имплементация на frontend тестове за DomOS Cashier MVP1 проекта.

**Цел**: Постигане на минимум 70% code coverage за критичните модули.

**Текущо състояние**:
- ✅ vitest.config.ts е конфигуриран
- ✅ src/test/setup.ts съществува
- ✅ src/test/test-utils.tsx съществува
- ❌ Липсват тестови файлове (*.test.ts/tsx)
- ❌ CI pipeline (npm run test:ci) fail-ва поради липса на тестове

---

## Фаза 1: Проверка и фиксване на конфигурацията

### Стъпка 1.1: Проверка на vitest.config.ts

```bash
cd /a0/usr/projects/domos/mvp1-cashier/frontend
cat vitest.config.ts
```

**Очаквана конфигурация**:
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        'src/main.tsx',
        'src/components/ui/**', // shadcn components - external
      ],
      all: false, // Важно: предотвратява parse errors за некласирани файлове
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

### Стъпка 1.2: Проверка на src/test/setup.ts

```bash
cat src/test/setup.ts
```

**Очаквано съдържание**:
```typescript
import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

afterEach(() => {
  cleanup()
})

// Mock matchMedia за responsive компоненти
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})
```

### Стъпка 1.3: Проверка на зависимостите

```bash
npm list @testing-library/react @testing-library/jest-dom vitest jsdom
```

**Ако липсват**:
```bash
npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event vitest jsdom
```

---

## Фаза 2: Тестове за Services (API Layer)

### Стъпка 2.1: Създаване на src/services/api.test.ts

**Приоритет**: Висок (core функционалност)

```typescript
// src/services/api.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('API Service', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('authApi', () => {
    describe('login', () => {
      it('should send correct login request', async () => {
        const mockResponse = {
          access_token: 'test-token',
          user: { id: 1, username: 'admin', role: 'admin' }
        }
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockResponse)
        })

        const { authApi } = await import('./api')
        const result = await authApi.login('admin', 'password')

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/auth/login'),
          expect.objectContaining({
            method: 'POST',
            body: expect.any(String)
          })
        )
        expect(result).toEqual(mockResponse)
      })

      it('should throw error on failed login', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: () => Promise.resolve({ detail: 'Invalid credentials' })
        })

        const { authApi } = await import('./api')
        await expect(authApi.login('wrong', 'wrong')).rejects.toThrow()
      })
    })

    describe('me', () => {
      it('should fetch current user with auth token', async () => {
        localStorage.setItem('token', 'test-token')
        const mockUser = { id: 1, username: 'admin', role: 'admin' }
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockUser)
        })

        const { authApi } = await import('./api')
        const result = await authApi.me()

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/auth/me'),
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': 'Bearer test-token'
            })
          })
        )
        expect(result).toEqual(mockUser)
      })
    })
  })

  describe('apartmentsApi', () => {
    it('should fetch all apartments', async () => {
      localStorage.setItem('token', 'test-token')
      const mockApartments = [
        { id: 1, number: '1', floor: 1, area: 50 },
        { id: 2, number: '2', floor: 1, area: 60 }
      ]
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApartments)
      })

      const { apartmentsApi } = await import('./api')
      const result = await apartmentsApi.getAll()

      expect(result).toEqual(mockApartments)
    })
  })

  describe('paymentsApi', () => {
    it('should create payment', async () => {
      localStorage.setItem('token', 'test-token')
      const paymentData = {
        apartment_id: 1,
        amount: 100,
        payment_method: 'cash'
      }
      const mockResponse = { id: 1, ...paymentData }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const { paymentsApi } = await import('./api')
      const result = await paymentsApi.create(paymentData)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/payments'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(paymentData)
        })
      )
      expect(result).toEqual(mockResponse)
    })
  })
})
```

---

## Фаза 3: Тестове за Context (State Management)

### Стъпка 3.1: Създаване на src/context/AuthContext.test.tsx

**Приоритет**: Висок (auth е критичен)

```typescript
// src/context/AuthContext.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from './AuthContext'

// Mock the API
vi.mock('../services/api', () => ({
  authApi: {
    login: vi.fn(),
    me: vi.fn(),
  }
}))

import { authApi } from '../services/api'

// Test component that uses useAuth
function TestComponent() {
  const { user, isAuthenticated, login, logout, loading } = useAuth()
  
  if (loading) return <div>Loading...</div>
  
  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? 'Authenticated' : 'Not authenticated'}
      </div>
      {user && <div data-testid="username">{user.username}</div>}
      <button onClick={() => login('admin', 'password')}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('should start as not authenticated', async () => {
    vi.mocked(authApi.me).mockRejectedValue(new Error('Not authenticated'))
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not authenticated')
    })
  })

  it('should authenticate user on login', async () => {
    const user = userEvent.setup()
    const mockUser = { id: 1, username: 'admin', role: 'admin' }
    
    vi.mocked(authApi.me).mockRejectedValue(new Error('Not authenticated'))
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: 'test-token',
      user: mockUser
    })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not authenticated')
    })

    await user.click(screen.getByText('Login'))

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated')
      expect(screen.getByTestId('username')).toHaveTextContent('admin')
    })
  })

  it('should restore session from token', async () => {
    localStorage.setItem('token', 'existing-token')
    const mockUser = { id: 1, username: 'admin', role: 'admin' }
    vi.mocked(authApi.me).mockResolvedValue(mockUser)

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated')
      expect(screen.getByTestId('username')).toHaveTextContent('admin')
    })
  })

  it('should clear session on logout', async () => {
    const user = userEvent.setup()
    localStorage.setItem('token', 'existing-token')
    const mockUser = { id: 1, username: 'admin', role: 'admin' }
    vi.mocked(authApi.me).mockResolvedValue(mockUser)

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated')
    })

    await user.click(screen.getByText('Logout'))

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not authenticated')
      expect(localStorage.getItem('token')).toBeNull()
    })
  })
})
```

### Стъпка 3.2: Създаване на src/context/ThemeContext.test.tsx

**Приоритет**: Нисък

```typescript
// src/context/ThemeContext.test.tsx
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider, useTheme } from './ThemeContext'

function TestComponent() {
  const { theme, setTheme } = useTheme()
  return (
    <div>
      <div data-testid="theme">{theme}</div>
      <button onClick={() => setTheme('dark')}>Dark</button>
      <button onClick={() => setTheme('light')}>Light</button>
    </div>
  )
}

describe('ThemeContext', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('should default to system theme', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )
    expect(screen.getByTestId('theme')).toHaveTextContent('system')
  })

  it('should change theme', async () => {
    const user = userEvent.setup()
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )

    await user.click(screen.getByText('Dark'))
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
  })
})
```

---

## Фаза 4: Тестове за Pages (Component Integration)

### Стъпка 4.1: Създаване на src/pages/Login.test.tsx

**Приоритет**: Висок

```typescript
// src/pages/Login.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { ThemeProvider } from '../context/ThemeContext'
import Login from './Login'

// Mock navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate
  }
})

// Mock API
vi.mock('../services/api', () => ({
  authApi: {
    login: vi.fn(),
    me: vi.fn(),
  }
}))

import { authApi } from '../services/api'

const renderLogin = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    vi.mocked(authApi.me).mockRejectedValue(new Error('Not authenticated'))
  })

  it('should render login form', async () => {
    renderLogin()

    await waitFor(() => {
      expect(screen.getByLabelText(/потребител/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/парола/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /вход/i })).toBeInTheDocument()
    })
  })

  it('should show error on invalid credentials', async () => {
    const user = userEvent.setup()
    vi.mocked(authApi.login).mockRejectedValue(new Error('Invalid credentials'))

    renderLogin()

    await waitFor(() => {
      expect(screen.getByLabelText(/потребител/i)).toBeInTheDocument()
    })

    await user.type(screen.getByLabelText(/потребител/i), 'wrong')
    await user.type(screen.getByLabelText(/парола/i), 'wrong')
    await user.click(screen.getByRole('button', { name: /вход/i }))

    await waitFor(() => {
      expect(screen.getByText(/грешка/i)).toBeInTheDocument()
    })
  })

  it('should navigate to dashboard on successful login', async () => {
    const user = userEvent.setup()
    const mockUser = { id: 1, username: 'admin', role: 'admin' }
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: 'test-token',
      user: mockUser
    })

    renderLogin()

    await waitFor(() => {
      expect(screen.getByLabelText(/потребител/i)).toBeInTheDocument()
    })

    await user.type(screen.getByLabelText(/потребител/i), 'admin')
    await user.type(screen.getByLabelText(/парола/i), 'password')
    await user.click(screen.getByRole('button', { name: /вход/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })
})
```

### Стъпка 4.2: Създаване на src/pages/Dashboard.test.tsx

**Приоритет**: Среден

```typescript
// src/pages/Dashboard.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { ThemeProvider } from '../context/ThemeContext'
import Dashboard from './Dashboard'

vi.mock('../services/api', () => ({
  authApi: {
    me: vi.fn(),
  },
  apartmentsApi: {
    getStatuses: vi.fn(),
  },
  paymentsApi: {
    getRecent: vi.fn(),
    getFundBalance: vi.fn(),
  }
}))

import { authApi, apartmentsApi, paymentsApi } from '../services/api'

const renderDashboard = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

describe('Dashboard Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('token', 'test-token')
    
    vi.mocked(authApi.me).mockResolvedValue({
      id: 1,
      username: 'admin',
      role: 'admin'
    })
    
    vi.mocked(apartmentsApi.getStatuses).mockResolvedValue([
      { id: 1, number: '1', balance: -50 },
      { id: 2, number: '2', balance: 0 }
    ])
    
    vi.mocked(paymentsApi.getRecent).mockResolvedValue([])
    vi.mocked(paymentsApi.getFundBalance).mockResolvedValue({ balance: 1000 })
  })

  it('should render dashboard with stats', async () => {
    renderDashboard()

    await waitFor(() => {
      expect(screen.getByText(/табло/i)).toBeInTheDocument()
    })
  })

  it('should display fund balance', async () => {
    renderDashboard()

    await waitFor(() => {
      expect(screen.getByText(/1000/)).toBeInTheDocument()
    })
  })
})
```

### Стъпка 4.3: Създаване на src/pages/Apartments.test.tsx

**Приоритет**: Среден

```typescript
// src/pages/Apartments.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { ThemeProvider } from '../context/ThemeContext'
import Apartments from './Apartments'

vi.mock('../services/api', () => ({
  authApi: {
    me: vi.fn(),
  },
  apartmentsApi: {
    getAll: vi.fn(),
    getStatuses: vi.fn(),
  }
}))

import { authApi, apartmentsApi } from '../services/api'

const renderApartments = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Apartments />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

describe('Apartments Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('token', 'test-token')
    
    vi.mocked(authApi.me).mockResolvedValue({
      id: 1,
      username: 'admin',
      role: 'admin'
    })
    
    vi.mocked(apartmentsApi.getAll).mockResolvedValue([
      { id: 1, number: '1', floor: 1, area: 50, monthly_fee: 25 },
      { id: 2, number: '2', floor: 1, area: 60, monthly_fee: 30 }
    ])
    
    vi.mocked(apartmentsApi.getStatuses).mockResolvedValue([
      { id: 1, number: '1', balance: -50 },
      { id: 2, number: '2', balance: 0 }
    ])
  })

  it('should render apartments list', async () => {
    renderApartments()

    await waitFor(() => {
      expect(screen.getByText(/апартаменти/i)).toBeInTheDocument()
    })
  })

  it('should display apartment numbers', async () => {
    renderApartments()

    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
    })
  })
})
```

### Стъпка 4.4: Създаване на src/pages/Payments.test.tsx

**Приоритет**: Висок

```typescript
// src/pages/Payments.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { ThemeProvider } from '../context/ThemeContext'
import Payments from './Payments'

vi.mock('../services/api', () => ({
  authApi: {
    me: vi.fn(),
  },
  paymentsApi: {
    getAll: vi.fn(),
  },
  apartmentsApi: {
    getAll: vi.fn(),
  }
}))

import { authApi, paymentsApi, apartmentsApi } from '../services/api'

const renderPayments = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Payments />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

describe('Payments Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('token', 'test-token')
    
    vi.mocked(authApi.me).mockResolvedValue({
      id: 1,
      username: 'admin',
      role: 'admin'
    })
    
    vi.mocked(paymentsApi.getAll).mockResolvedValue([
      {
        id: 1,
        apartment_id: 1,
        amount: 50,
        payment_method: 'cash',
        created_at: '2026-01-15T10:00:00Z'
      }
    ])
    
    vi.mocked(apartmentsApi.getAll).mockResolvedValue([
      { id: 1, number: '1', floor: 1, area: 50, monthly_fee: 25 }
    ])
  })

  it('should render payments list', async () => {
    renderPayments()

    await waitFor(() => {
      expect(screen.getByText(/плащания/i)).toBeInTheDocument()
    })
  })

  it('should display payment amount', async () => {
    renderPayments()

    await waitFor(() => {
      expect(screen.getByText(/50/)).toBeInTheDocument()
    })
  })
})
```

---

## Фаза 5: Тестове за Hooks

### Стъпка 5.1: Създаване на src/hooks/use-toast.test.ts

**Приоритет**: Нисък

```typescript
// src/hooks/use-toast.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useToast } from './use-toast'

describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should add toast', () => {
    const { result } = renderHook(() => useToast())

    act(() => {
      result.current.toast({
        title: 'Test',
        description: 'Test description'
      })
    })

    expect(result.current.toasts).toHaveLength(1)
    expect(result.current.toasts[0].title).toBe('Test')
  })

  it('should dismiss toast', () => {
    const { result } = renderHook(() => useToast())

    act(() => {
      result.current.toast({ title: 'Test' })
    })

    const toastId = result.current.toasts[0].id

    act(() => {
      result.current.dismiss(toastId)
    })

    expect(result.current.toasts).toHaveLength(0)
  })
})
```

---

## Фаза 6: Конфигурация и CI интеграция

### Стъпка 6.1: Актуализиране на vitest.config.ts

**КРИТИЧНО**: Добавяне на `coverage.all: false` за да се предотвратят parse errors.

```bash
cat > vitest.config.ts << 'EOF'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: ['node_modules', 'dist', 'src/components/ui/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        'src/main.tsx',
        'src/vite-env.d.ts',
        'src/components/ui/**',
      ],
      // ВАЖНО: Това предотвратява parse errors за файлове без тестове
      all: false,
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
EOF
```

### Стъпка 6.2: Актуализиране на src/test/setup.ts

```bash
cat > src/test/setup.ts << 'EOF'
import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock scrollTo
window.scrollTo = vi.fn()
EOF
```

### Стъпка 6.3: Проверка на package.json scripts

```bash
# Проверка че test scripts са правилно конфигурирани
cat package.json | grep -A5 '"scripts"'
```

**Очаквано**:
```json
"scripts": {
  "test": "vitest",
  "test:ci": "vitest run --coverage",
  "test:watch": "vitest --watch"
}
```

---

## Фаза 7: Изпълнение и Верификация

### Стъпка 7.1: Локално тестване

```bash
cd /a0/usr/projects/domos/mvp1-cashier/frontend

# Инсталиране на зависимости ако липсват
npm install

# Стартиране на тестовете
npm run test

# Стартиране с coverage
npm run test:ci
```

### Стъпка 7.2: CI проверка

```bash
# Push промените и провери CI
git add .
git commit -m "feat(frontend): add unit tests for services, context, pages, and hooks"
git push
```

---

## Обобщение: Чеклист за изпълнение

### Приоритет 1 (Критични - трябва да минат CI)

- [ ] **Стъпка 1.1**: Проверка и фиксване на vitest.config.ts (добави `coverage.all: false`)
- [ ] **Стъпка 1.2**: Проверка на src/test/setup.ts (добави mocks)
- [ ] **Стъпка 2.1**: Създаване на src/services/api.test.ts

### Приоритет 2 (Високо важни)

- [ ] **Стъпка 3.1**: Създаване на src/context/AuthContext.test.tsx
- [ ] **Стъпка 4.1**: Създаване на src/pages/Login.test.tsx
- [ ] **Стъпка 4.4**: Създаване на src/pages/Payments.test.tsx

### Приоритет 3 (Средно важни)

- [ ] **Стъпка 4.2**: Създаване на src/pages/Dashboard.test.tsx
- [ ] **Стъпка 4.3**: Създаване на src/pages/Apartments.test.tsx

### Приоритет 4 (Ниско важни)

- [ ] **Стъпка 3.2**: Създаване на src/context/ThemeContext.test.tsx
- [ ] **Стъпка 5.1**: Създаване на src/hooks/use-toast.test.ts

---

## Файлова структура след имплементация

```
frontend/src/
├── services/
│   ├── api.ts
│   └── api.test.ts              ← НОВО
├── context/
│   ├── AuthContext.tsx
│   ├── AuthContext.test.tsx     ← НОВО
│   ├── ThemeContext.tsx
│   └── ThemeContext.test.tsx    ← НОВО
├── pages/
│   ├── Login.tsx
│   ├── Login.test.tsx           ← НОВО
│   ├── Dashboard.tsx
│   ├── Dashboard.test.tsx       ← НОВО
│   ├── Apartments.tsx
│   ├── Apartments.test.tsx      ← НОВО
│   ├── Payments.tsx
│   └── Payments.test.tsx        ← НОВО
├── hooks/
│   ├── use-toast.ts
│   └── use-toast.test.ts        ← НОВО
└── test/
    ├── setup.ts                 ← АКТУАЛИЗИРАН
    ├── test-utils.tsx
    └── vitest.d.ts
```

---

## Бележки за агента-изпълнител

1. **Започни с Приоритет 1** - това е минимумът за CI да мине
2. **Винаги проверявай съществуващия код** преди да пишеш тестове
3. **Използвай `vi.mock()`** за API calls, не правете реални заявки
4. **Тествай happy path първо**, после edge cases
5. **Ако тест fail-ва**, провери дали mock-овете са правилни
6. **След всяка фаза** пусни `npm run test:ci` за да провериш прогреса

---

## Очакван резултат

След изпълнение на плана:
- CI pipeline ще минава успешно
- Coverage ще е минимум 50% за критичните модули
- Няма да има parse errors от Rolldown
- Тестовете ще верифицират основната функционалност