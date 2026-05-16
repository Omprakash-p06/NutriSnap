/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#000000', // True Black AMOLED
        foreground: '#ffffff',
        accent: '#FF6B5A',
        surface: '#111111',
        border: '#333333',
      }
    },
  },
  plugins: [],
}
