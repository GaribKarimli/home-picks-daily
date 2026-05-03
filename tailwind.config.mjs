/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#F5F7F5',
          100: '#E8EDE8',
          200: '#D0DBD0',
          300: '#A9BDA9',
          400: '#7A9A7A',
          500: '#4A7C59',
          600: '#3D6649',
          700: '#305239',
          800: '#27422E',
          900: '#1E3524',
        },
        accent: {
          50: '#F9F0EB',
          100: '#F3E1D6',
          200: '#E8C3AD',
          300: '#DCA585',
          400: '#D1865C',
          500: '#C17A5A',
          600: '#A36549',
          700: '#85513B',
          800: '#663E2D',
          900: '#482B1F',
        },
        cream: '#FAF8F6',
        dark: '#1C1C1E',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
