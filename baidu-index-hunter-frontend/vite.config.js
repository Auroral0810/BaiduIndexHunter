import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue({
      // 启用.vue文件中的TypeScript
      script: {
        defineModel: true,
        propsDestructure: true
      }
    })
  ],
  optimizeDeps: {
    include: ['vue'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    },
    extensions: ['.js', '.ts', '.vue', '.json']
  }
})
