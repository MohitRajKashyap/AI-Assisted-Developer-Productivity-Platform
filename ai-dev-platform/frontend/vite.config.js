import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/health': 'http://localhost:8000',
      '/dashboard': 'http://localhost:8000',
      '/prompts': 'http://localhost:8000',
      '/bugs': 'http://localhost:8000',
      '/pr': 'http://localhost:8000',
      '/errors': 'http://localhost:8000',
      '/evaluations': 'http://localhost:8000',
      '/agents': 'http://localhost:8000',
      '/context': 'http://localhost:8000',
    }
  }
})
