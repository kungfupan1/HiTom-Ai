import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 8080,
    proxy: {
      '/api': {
        // 👇 重点：将 localhost 改为 127.0.0.1，端口必须是 8000
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/auth': {
        // 👇 这里也要改
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/users': {
        // 👇 还有这里
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})