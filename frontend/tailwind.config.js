/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--bg)',
        foreground: 'var(--text)',
        accent: 'var(--accent)',
        surface: 'var(--surface)',
        border: 'var(--border-color)',
        zinc: {
          50: 'var(--zinc-50)',
          100: 'var(--zinc-100)',
          200: 'var(--zinc-200)',
          300: 'var(--zinc-300)',
          400: 'var(--zinc-400)',
          500: 'var(--zinc-500)',
          600: 'var(--zinc-600)',
          700: 'var(--zinc-700)',
          800: 'var(--zinc-800)',
          900: 'var(--zinc-900)',
          950: 'var(--zinc-950)',
        }
      }
    },
  },
  plugins: [],
}
