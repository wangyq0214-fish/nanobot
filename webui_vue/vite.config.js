import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const target = process.env.NANOBOT_API_URL ?? 'http://127.0.0.1:8765'
const wsTarget = target.replace(/^http/, 'ws')

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    hmr: { host: '127.0.0.1', port: 5174 },
    proxy: {
      '/webui': { target, changeOrigin: true },
      '/api': { target, changeOrigin: true },
      '/': {
        target: wsTarget,
        ws: true,
        changeOrigin: true,
        bypass: (req) =>
          req.headers.upgrade === 'websocket' ? undefined : req.url,
      },
    },
  },
})
