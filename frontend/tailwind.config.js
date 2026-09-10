/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#060a0f',
        s0: '#080d14',
        s1: '#0b1118',
        s2: '#0f1822',
        s3: '#14202e',
        s4: '#1a2a3c',
        cyan: {
          DEFAULT: '#00e5b8',
          2: '#00b896',
          d: 'rgba(0,229,184,0.10)',
          dd: 'rgba(0,229,184,0.05)',
          glow: 'rgba(0,229,184,0.18)'
        },
        red: {
          DEFAULT: '#ff4757',
          2: '#e03445',
          d: 'rgba(255,71,87,0.12)',
          glow: 'rgba(255,71,87,0.20)'
        },
        amber: {
          DEFAULT: '#ffa726',
          d: 'rgba(255,167,38,0.12)'
        },
        blue: {
          DEFAULT: '#4dabf7',
          d: 'rgba(77,171,247,0.12)'
        },
        violet: {
          DEFAULT: '#b197fc',
          d: 'rgba(177,151,252,0.12)'
        },
        green: {
          DEFAULT: '#2ed573',
          d: 'rgba(46,213,115,0.12)'
        },
        tx: '#e8eef8',
        tx2: '#7a8fa6',
        tx3: '#3d5068',
        tx4: '#475669',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        rad: '12px',
        rad2: '8px',
        rad3: '6px',
      }
    },
  },
  plugins: [
    require('daisyui')
  ],
  daisyui: {
    themes: [
      {
        darkCommand: {
          "primary": "#00e5b8",
          "secondary": "#4dabf7",
          "accent": "#b197fc",
          "neutral": "#0f1822",
          "base-100": "#060a0f",
          "info": "#4dabf7",
          "success": "#2ed573",
          "warning": "#ffa726",
          "error": "#ff4757",
        },
      },
    ],
    darkTheme: "darkCommand",
    base: false,
  }
}
