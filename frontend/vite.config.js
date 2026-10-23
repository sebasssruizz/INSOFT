import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command, mode }) => {
  // El build de producción (Vercel) no puede salir sin backend configurado:
  // sin VITE_API_URL el frontend no tendría a dónde llamar.
  if (command === 'build' && mode === 'production') {
    const env = loadEnv(mode, process.cwd(), 'VITE_')
    if (!env.VITE_API_URL) {
      throw new Error(
        'Falta VITE_API_URL: define la URL pública del backend antes de compilar para producción.',
      )
    }
  }

  return {
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
  }
})
