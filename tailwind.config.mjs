/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#F0F5F2',
          100: '#DCEBE2',
          200: '#B9D7C5',
          300: '#8FB5A3',
          400: '#6A9B84',
          500: '#4A7C59',
          600: '#3D6649',
          700: '#305239',
          800: '#27422E',
          900: '#1E3524',
        },
        accent: {
          50: '#FDF0EE',
          100: '#F9DDD8',
          200: '#F3BBB1',
          300: '#ED9989',
          400: '#E07762',
          500: '#D4A5A5',
          600: '#C48F8F',
          700: '#A66D6D',
          800: '#885050',
          900: '#6A3838',
        },
        cream: '#FDF8F4',
        dark: '#2C2C2C',
        blush: '#FDF0EE',
        sage: '#F0F5F2',
        gold: '#C9A96E',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Playfair Display', 'Georgia', 'serif'],
      },
      boxShadow: {
        'soft': '0 4px 20px rgba(0, 0, 0, 0.06)',
        'soft-lg': '0 8px 32px rgba(0, 0, 0, 0.08)',
        'soft-xl': '0 12px 48px rgba(0, 0, 0, 0.1)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
