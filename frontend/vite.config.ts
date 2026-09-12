import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  },
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-tf': ['@tensorflow/tfjs', '@tensorflow-models/coco-ssd'],
          'vendor-react': ['react', 'react-dom']
        }
      }
    }
  }
});
