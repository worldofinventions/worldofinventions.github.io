import { defineConfig } from 'vite';

// Сборка попадает в ru/miniapp/web — эту папку отдаёт ru/server.py под /ru/,
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
    // Сервер отдаёт русский музей под /ru/, поэтому пути переписываются.
    proxy: {
      '/api': { target: 'http://localhost:10000', rewrite: (path) => `/ru${path}` },
      '/exhibits': { target: 'http://localhost:10000', rewrite: (path) => `/ru${path}` },
    },
  },
});
