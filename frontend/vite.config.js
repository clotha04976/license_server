import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    global: 'globalThis',
    'process.env': '{}',
  },
  resolve: {
    alias: {
      crypto: 'crypto-browserify',
      stream: 'stream-browserify',
      buffer: 'buffer',
      process: 'process/browser',
    },
  },
  // 修正 Vite 與 Node.js 模組的兼容性問題
  optimizeDeps: {
    include: ['crypto-browserify', 'stream-browserify', 'buffer', 'process'],
    force: true,
    esbuildOptions: {
      define: {
        global: 'globalThis',
      },
    },
  },
  // 修正建置配置
  build: {
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true,
    },
    rollupOptions: {
      external: [],
    },
  },
  server: {
    host: '0.0.0.0', // 允許外部訪問
    port: 5173,
    allowedHosts: [
      'lic.shinping.synology.me', // 允許您的網址
      'localhost',                // (可選) 確保本地連線也允許
      '192.168.1.133'             // (可選) 確保 NAS IP 連線也允許
    ],
    watch: {
      usePolling: true, // 在 Docker 容器中使用輪詢監聽檔案變化
    },
    // 支援 SPA 路由的 history API fallback
    historyApiFallback: {
      index: '/index.html'
    },
    // 設定代理到後端 API
    proxy: {
      '/api': {
        target: process.env.NODE_ENV === 'development' 
          ? 'http://license_server_backend:8000'  // Docker 容器環境
          : 'http://localhost:8000',              // 本地開發環境
        changeOrigin: true,
        secure: false,
      },
    },
  }
})
