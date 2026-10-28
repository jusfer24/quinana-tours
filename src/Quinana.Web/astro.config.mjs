// @ts-check
import { defineConfig } from 'astro/config';

import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  integrations: [react()],

  // El acceso (Comenzar / Crear una cuenta) es ahora la página principal.
  redirects: {
    '/login': '/',
  },

  vite: {
    plugins: [tailwindcss()]
  }
});