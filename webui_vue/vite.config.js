import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const target = process.env.NANOBOT_API_URL ?? 'http://127.0.0.1:8765'
const apiTarget = process.env.NANOBOT_HTTP_URL ?? 'http://127.0.0.1:8767'
const wsTarget = target.replace(/^http/, 'ws')
const latexTarget = process.env.LATEX_API_URL ?? 'http://10.100.132.162:8001'

export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-vue': ['vue', 'vue-router'],
          'vendor-echarts': ['echarts'],
        }
      }
    }
  },
  server: {
    port: 5173,
    hmr: { host: '127.0.0.1', port: 5174 },
    proxy: {
      '/webui': { target, changeOrigin: true },
      '/api': { target: apiTarget, changeOrigin: true },
      '/compile': { target: latexTarget, changeOrigin: true },
      '/compile-with-files': { target: latexTarget, changeOrigin: true },
      '/': {
        target: wsTarget,
        ws: true,
        changeOrigin: true,
        bypass: (req) => {
          // Only proxy WebSocket requests to wsTarget
          // For non-WebSocket requests, let Vite handle them (SPA routing, etc.)
          if (req.headers.upgrade === 'websocket') {
            return undefined  // Continue with proxy to wsTarget
          }
          return req.url  // Skip proxy, let Vite handle
        },
      },
    },
  },
})
