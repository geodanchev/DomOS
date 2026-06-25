import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      usePolling: true,
    },
    proxy: {
      '/api': {
        // In Docker: use 'backend' service name. Locally: use localhost
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
