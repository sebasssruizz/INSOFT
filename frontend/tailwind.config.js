/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont',
          '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif',
        ],
      },
      boxShadow: {
        // Sombras tintadas con el verde de marca, en vez de negro puro
        'ins-sm': '0 1px 2px 0 rgb(0 112 99 / 0.08)',
        'ins-md': '0 8px 24px -6px rgb(0 112 99 / 0.16)',
        'ins-lg': '0 20px 48px -12px rgb(0 84 73 / 0.24)',
      },
      colors: {
        // INS — Instrumentación Quirúrgica (verde quirúrgico)
        ins: {
          50: '#eafaf5',
          100: '#d0f3e8',
          200: '#a0e6d0',
          300: '#5fd4b0',
          400: '#2bb88e',
          500: '#00a896',
          600: '#008f7d',
          700: '#007063',
          800: '#005449',
          900: '#003d35',
        },
        // OFT — Oftalmología (azul quirúrgico)
        oft: {
          50: '#f0f7fc',
          100: '#dcedf7',
          200: '#b3d7ee',
          300: '#7bbce1',
          400: '#3e9bd3',
          500: '#0077b6',
          600: '#006099',
          700: '#004a77',
          800: '#003659',
          900: '#002540',
        },
        // Quirófano — neutros quirúrgicos
        surgery: {
          50: '#f7fbfc',
          100: '#eef5f8',
          200: '#dce8ef',
          300: '#c0d4df',
          400: '#9cb7c9',
          500: '#7a98ad',
          600: '#5f7e95',
          700: '#4b657a',
          800: '#3f5366',
          900: '#364756',
        },
      },
    },
  },
  plugins: [],
}
