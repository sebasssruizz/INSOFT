import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
  },
  // @testing-library/auto-cleanup requiere globals desde el plugin de vitest;
  // lo resolvemos con el API explícita del paquete si el entorno no la cargó.
})
