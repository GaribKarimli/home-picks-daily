import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://home-picks-daily.vercel.app',
  integrations: [
    tailwind(),
    sitemap(),
  ],
});
