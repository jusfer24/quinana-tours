// @ts-check
import { defineConfig, fontProviders } from 'astro/config';

import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';
import { loadEnv } from 'vite';

// Las fotos del catálogo se suben en el CRM y Django las sirve. Astro las descarga al compilar
// y las optimiza como las locales (<Image/>), así que hay que autorizar el dominio de la API.
const env = loadEnv(process.env.NODE_ENV ?? 'development', process.cwd(), '');
const catalogApi = new URL(env.CATALOG_API_URL || env.PUBLIC_API_URL || 'http://localhost:8000');

// https://astro.build/config
export default defineConfig({
  // Dominio público: lo usan las etiquetas hreflang. Cambiarlo cuando haya dominio propio.
  site: 'https://quinana-tours.pages.dev',

  integrations: [react()],

  image: {
    remotePatterns: [
      { protocol: catalogApi.protocol.replace(':', ''), hostname: catalogApi.hostname },
      { protocol: 'http', hostname: 'localhost' },
      { protocol: 'http', hostname: '127.0.0.1' },
    ],
  },

  // Sitio bilingüe: español en la raíz (/) e inglés en /en/.
  i18n: {
    locales: ['es', 'en'],
    defaultLocale: 'es',
    routing: { prefixDefaultLocale: false },
  },

  // Fuentes descargadas al compilar y servidas desde el propio sitio (sin Google Fonts).
  fonts: [
    {
      provider: fontProviders.fontsource(),
      name: 'Bricolage Grotesque',
      cssVariable: '--font-bricolage',
      weights: ['600 800'],
      subsets: ['latin'],
      fallbacks: ['sans-serif'],
    },
    {
      provider: fontProviders.fontsource(),
      name: 'Instrument Sans',
      cssVariable: '--font-instrument',
      weights: ['400 600'],
      styles: ['normal'],
      subsets: ['latin'],
      fallbacks: ['sans-serif'],
    },
  ],

  vite: {
    plugins: [tailwindcss()]
  }
});
