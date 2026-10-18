/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        heading: ['Outfit', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        twin: {
          dark: '#030712',
          surface: '#0f172a',
          card: '#1e293b',
          border: 'rgba(148, 163, 184, 0.1)',
          cyan: '#06b6d4',
          sky: '#38bdf8',
          blue: '#3b82f6',
          indigo: '#6366f1',
        },
        hazard: {
          flood: '#0284c7',
          heatwave: '#f97316',
          drought: '#eab308',
          wildfire: '#ef4444',
          rainfall: '#8b5cf6',
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}

