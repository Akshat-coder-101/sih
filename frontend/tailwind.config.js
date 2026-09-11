/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Watermelon Command Tokens
        ink: {
          950: '#101313',
          900: '#171b1a',
          850: '#1c2220',
          800: '#202624',
          700: '#293430',
        },
        rind: {
          100: '#f2f5ee',
          200: '#d9e0d6',
          300: '#b6c1b7',
          500: '#718077',
          600: '#4e5a53',
        },
        melon: {
          DEFAULT: '#ff6b5f',
          500: '#ff6b5f',
          600: '#e84d52',
          700: '#c7383d',
          d: 'rgba(255, 107, 95, 0.12)',
          dd: 'rgba(255, 107, 95, 0.06)',
          glow: 'rgba(255, 107, 95, 0.22)',
        },
        seed: {
          950: '#241217',
          900: '#351d24',
          800: '#4d242f',
        },
        leaf: {
          DEFAULT: '#65d68b',
          500: '#65d68b',
          600: '#4cb870',
          900: '#193126',
          d: 'rgba(101, 214, 139, 0.12)',
          dd: 'rgba(101, 214, 139, 0.06)',
          glow: 'rgba(101, 214, 139, 0.22)',
        },
        instrument: {
          DEFAULT: '#56c7d9',
          400: '#56c7d9',
          500: '#38b2c6',
          d: 'rgba(86, 199, 217, 0.12)',
          dd: 'rgba(86, 199, 217, 0.06)',
          glow: 'rgba(86, 199, 217, 0.20)',
        },
        warning: {
          DEFAULT: '#f4bd5b',
          400: '#f4bd5b',
          500: '#e5a538',
          d: 'rgba(244, 189, 91, 0.12)',
          glow: 'rgba(244, 189, 91, 0.20)',
        },
        // Mapped Aliases for Shell Continuity
        bg: '#101313',
        s0: '#131716',
        s1: '#171b1a',
        s2: '#202624',
        s3: '#293430',
        s4: '#33403c',
        cyan: {
          DEFAULT: '#56c7d9',
          2: '#38b2c6',
          d: 'rgba(86,199,217,0.12)',
          dd: 'rgba(86,199,217,0.06)',
          glow: 'rgba(86,199,217,0.20)'
        },
        red: {
          DEFAULT: '#ff6b5f',
          2: '#e84d52',
          d: 'rgba(255,107,95,0.12)',
          glow: 'rgba(255,107,95,0.22)'
        },
        amber: {
          DEFAULT: '#f4bd5b',
          d: 'rgba(244,189,91,0.12)'
        },
        blue: {
          DEFAULT: '#56c7d9',
          d: 'rgba(86,199,217,0.12)'
        },
        violet: {
          DEFAULT: '#b197fc',
          d: 'rgba(177,151,252,0.12)'
        },
        green: {
          DEFAULT: '#65d68b',
          d: 'rgba(101,214,139,0.12)'
        },
        tx: '#f2f5ee',
        tx2: '#b6c1b7',
        tx3: '#718077',
        tx4: '#4e5a53',
      },
      fontFamily: {
        sans: ['DM Sans', 'Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        rad: '10px',
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
        watermelonCommand: {
          "primary": "#ff6b5f",
          "secondary": "#56c7d9",
          "accent": "#65d68b",
          "neutral": "#202624",
          "base-100": "#101313",
          "info": "#56c7d9",
          "success": "#65d68b",
          "warning": "#f4bd5b",
          "error": "#e84d52",
        },
      },
    ],
    darkTheme: "watermelonCommand",
    base: false,
  }
}
