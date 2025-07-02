import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => false,
          whitespace: 'preserve'
        }
      },
      script: {
        defineModel: true,
        propsDestructure: true
      }
    })
  ],
  optimizeDeps: {
    include: ['vue', 'axios', 'element-plus'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    },
    extensions: ['.js', '.ts', '.vue', '.json']
  },
  server: {
    host: true,
    port: 5173,
    strictPort: false,
    open: false,
    cors: true
  }
})
