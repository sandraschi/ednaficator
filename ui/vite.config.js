import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['goliath'],
    port: 10943,
    strictPort: true,
    host: 'localhost',
    proxy: {
      '/api': {
        target: 'http://localhost:10942',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:10942',
        ws: true,
        changeOrigin: true,
      },
    }
  },
  build: {
    outDir: 'dist'
  }
})
