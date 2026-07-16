/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

// ESM-compatible __dirname
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export default defineConfig({
  plugins: [
    react(),
  ],
  resolve: {
    // Use Vite 8's native tsconfig paths support (recommended for vitest 4.x)
    tsconfigPaths: true,
    // Fallback alias using __dirname for maximum compatibility
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: ['node_modules', 'dist', 'src/components/ui/**'],
    // Explicit alias in test config for vitest 4.x
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
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
        'src/components/Layout.tsx',
        'src/components/NewPaymentDialog.tsx',
        'src/components/PaymentModal.tsx',
        'src/components/NewObligationDialog.tsx',
        'src/components/PermissionGate.tsx',
      ],
      all: false,
    },
  },
})
