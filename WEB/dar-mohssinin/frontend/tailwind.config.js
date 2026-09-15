/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Syne"', 'sans-serif'],
        body: ['"DM Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        pitch: {
          bg:      '#0a0a0f',
          surface: '#111118',
          card:    '#16161f',
          border:  '#1e1e2e',
          accent:  '#7c3aed',
          glow:    '#a855f7',
          text:    '#e2e8f0',
          muted:   '#64748b',
          success: '#10b981',
          danger:  '#ef4444',
          warn:    '#f59e0b',
        },
      },
      boxShadow: {
        'glow-sm': '0 0 12px rgba(124,58,237,0.3)',
        'glow-md': '0 0 24px rgba(124,58,237,0.4)',
        'glow-lg': '0 0 48px rgba(124,58,237,0.25)',
      },
      animation: {
        'fade-in':    'fadeIn 0.4s ease forwards',
        'slide-up':   'slideUp 0.35s ease forwards',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'typing':     'typing 1.2s steps(3) infinite',
      },
      keyframes: {
        fadeIn:  { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: 'translateY(16px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        typing:  { '0%,100%': { content: '"·"' }, '33%': { content: '"··"' }, '66%': { content: '"···"' } },
      },
    },
  },
  plugins: [],
}
