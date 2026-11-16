import { defineConfig } from 'vite';

// The build lands in miniapp/web — exactly the folder miniapp/server.py serves,
// so `npm run build` here and the mini app is live on the server.
export default defineConfig({
  base: './',
  build: {
    outDir: '../web',
    emptyOutDir: true,
  },
  server: {
    port: 5174,
    // In `vite` dev mode the API and the exhibit photos are taken from the
    // mini app server: run it first (`python miniapp/server.py`).
    proxy: {
      '/api': 'http://localhost:10000',
      '/exhibits': 'http://localhost:10000',
    },
  },
});
