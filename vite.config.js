import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendTarget = 'http://127.0.0.1:8000'

  return {
    plugins: [react()],
    server: {
      port: 5176,
      strictPort: true,
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true,
          secure: false,
          headers: {
            'ngrok-skip-browser-warning': 'true',
            'bypass-tunnel-reminder': 'true'
          }
        }
      }
    }
  }
})
