/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [
    react(),
    tsconfigPaths(),
  ],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: ['node_modules', 'dist', 'src/components/ui/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        'src/main.tsx',
        'src/vite-env.d.ts',
        'src/components/ui/**',
        // Exclude components that cause Rolldown parser issues
        'src/components/Layout.tsx',
        'src/components/NewPaymentDialog.tsx',
        'src/components/PaymentModal.tsx',
        'src/components/NewObligationDialog.tsx',
        'src/components/PermissionGate.tsx',
      ],
      // ВАЖНО: Това предотвратява parse errors за файлове без тестове
      all: false,
    },
  },
})
