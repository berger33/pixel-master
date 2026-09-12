import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Em docker-compose o backend é alcançado pelo nome do serviço; localmente,
// o padrão 127.0.0.1:8000 continua valendo.
const backend = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': { target: backend, changeOrigin: true },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': { target: backend, changeOrigin: true },
    },
  },
})
