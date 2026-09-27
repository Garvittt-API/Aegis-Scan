/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Cyberpunk Design System Colors
        background: '#0a0a0f',
        foreground: '#e0e0e0',
        card: '#12121a',
        muted: '#1c1c2e',
        mutedForeground: '#6b7280',
        accent: {
          DEFAULT: '#00ff88',
          secondary: '#ff00ff',
          tertiary: '#00d4ff',
        },
        border: '#2a2a3a',
        input: '#12121a',
        ring: '#00ff88',
        destructive: '#ff3366',

        // Legacy dark shades mapped for smooth backwards-compatibility
        dark: {
          50: '#f8fafc',
          100: '#e0e0e0',
          200: '#cbd5e1',
          300: '#94a3b8',
          400: '#6b7280',
          500: '#475569',
          600: '#334155',
          700: '#2a2a3a',
          800: '#1c1c2e',
          900: '#12121a',
          950: '#0a0a0f',
        },

        // Severity Indicators
        critical: '#ff3366',
        high: '#f97316',
        medium: '#eab308',
        low: '#00d4ff',
        informational: '#6b7280',
      },
      fontFamily: {
        heading: ['Orbitron', 'Share Tech Mono', 'monospace'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        accent: ['Share Tech Mono', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'neon': '0 0 5px #00ff88, 0 0 12px rgba(0, 255, 136, 0.3)',
        'neon-sm': '0 0 3px #00ff88, 0 0 6px rgba(0, 255, 136, 0.2)',
        'neon-lg': '0 0 10px #00ff88, 0 0 20px rgba(0, 255, 136, 0.4), 0 0 40px rgba(0, 255, 136, 0.15)',
        'neon-secondary': '0 0 5px #ff00ff, 0 0 15px rgba(255, 0, 255, 0.35)',
        'neon-tertiary': '0 0 5px #00d4ff, 0 0 15px rgba(0, 212, 255, 0.35)',
      },
      keyframes: {
        blink: {
          '50%': { opacity: '0' },
        },
        glitch: {
          '0%, 100%': { transform: 'translate(0)' },
          '20%': { transform: 'translate(-2px, 2px)' },
          '40%': { transform: 'translate(2px, -2px)' },
          '60%': { transform: 'translate(-1px, -1px)' },
          '80%': { transform: 'translate(1px, 1px)' },
        },
        rgbShift: {
          '0%, 100%': { textShadow: '-2px 0 #ff00ff, 2px 0 #00d4ff' },
          '50%': { textShadow: '2px 0 #ff00ff, -2px 0 #00d4ff' },
        },
      },
      animation: {
        blink: 'blink 1s step-end infinite',
        glitch: 'glitch 2s ease-in-out infinite',
        rgbShift: 'rgbShift 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
