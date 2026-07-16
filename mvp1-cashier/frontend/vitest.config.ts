/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'
import path from 'path'

// Use process.cwd() which is more reliable in CI environments
const rootDir = process.cwd()

export default defineConfig({
  plugins: [
    react(),
    tsconfigPaths({ root: rootDir }),
  ],
  resolve: {
    alias: [
      { find: /^@\/(.*)/, replacement: path.join(rootDir, 'src/$1') },
    ],
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: ['node_modules', 'dist', 'src/components/ui/**'],
    // Use server.deps for module resolution in vitest 4.x
    server: {
      deps: {
        inline: [/^(?!.*node_modules).*$/],
      },
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
