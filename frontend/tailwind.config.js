/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        // Newsreader: titulares y prosa académica. Manrope: interfaz y datos.
        display: ['"Newsreader Variable"', 'Newsreader', 'Georgia', 'serif'],
        sans: ['"Manrope Variable"', 'Manrope', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        // Escala primaria de marca.
        blue: {
          50: '#e8f3ff',
          100: '#d5e9ff',
          200: '#b3d4ff',
          300: '#85b7ff',
          400: '#568eff',
          500: '#2f65ff',
          600: '#0c39ff',
          700: '#002aff',
          800: '#062acd',
          900: '#102d9f',
          950: '#0a195c',
        },
        // Neutros ligeramente cálidos: dan un fondo de papel, no de pantalla fría.
        ink: {
          50: '#faf9f6',
          100: '#f3f1ec',
          200: '#e6e3dc',
          300: '#cfcbc2',
          400: '#a3a099',
          500: '#7b7973',
          600: '#5d5b57',
          700: '#454341',
          800: '#2c2b2a',
          900: '#1a1a19',
          950: '#0e0e0d',
        },
        // Tintes pastel de superficie. Nunca para texto ni para acciones:
        // solo colorean tarjetas, medallones e ilustraciones de fondo.
        soft: {
          lavender: '#efeaff',
          sky: '#e4f1fe',
          mint: '#e4f6ec',
          butter: '#fdf2dc',
          peach: '#feeade',
          rose: '#fdeaf1',
        },
        // Contrapartes legibles de los tintes pastel, para iconos y cifras.
        deep: {
          lavender: '#5b3fc4',
          sky: '#1f6fb2',
          mint: '#1e7a52',
          butter: '#9a6b12',
          peach: '#b85a2a',
          rose: '#b5386e',
        },
        // Solo para retroalimentación de las preguntas y acciones destructivas.
        correct: { 50: '#eaf7f1', 200: '#b6e0cd', 500: '#12855f', 700: '#0a5a40' },
        wrong: { 50: '#fdeef0', 200: '#f4c4cb', 500: '#c02b3f', 700: '#8d1c2c' },
      },
      boxShadow: {
        e1: '0 1px 2px 0 rgb(28 27 26 / 0.05), 0 1px 1px -1px rgb(28 27 26 / 0.03)',
        e2: '0 4px 14px -3px rgb(28 27 26 / 0.07), 0 2px 4px -2px rgb(28 27 26 / 0.04)',
        e3: '0 18px 40px -14px rgb(28 27 26 / 0.14), 0 6px 14px -8px rgb(28 27 26 / 0.07)',
        e4: '0 32px 64px -20px rgb(28 27 26 / 0.22)',
        'blue-glow': '0 10px 26px -10px rgb(16 45 159 / 0.42)',
      },
      transitionTimingFunction: {
        // Salidas exponenciales: rápidas al inicio, asentadas al final.
        out: 'cubic-bezier(0.16, 1, 0.3, 1)',
        'out-quart': 'cubic-bezier(0.25, 1, 0.5, 1)',
      },
      keyframes: {
        'rise-in': {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.97)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
        'drift-slow': {
          '0%, 100%': { transform: 'translate3d(0,0,0)' },
          '50%': { transform: 'translate3d(0,-14px,0)' },
        },
      },
      animation: {
        'rise-in': 'rise-in 0.55s cubic-bezier(0.16, 1, 0.3, 1) both',
        'fade-in': 'fade-in 0.4s ease-out both',
        'scale-in': 'scale-in 0.35s cubic-bezier(0.16, 1, 0.3, 1) both',
        shimmer: 'shimmer 1.6s infinite',
        'drift-slow': 'drift-slow 9s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
