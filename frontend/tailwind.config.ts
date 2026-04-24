import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Text"',
          '"SF Pro Display"',
          'Inter',
          '"Helvetica Neue"',
          'Helvetica',
          'Arial',
          'sans-serif',
        ],
        display: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Display"',
          '"Inter Tight"',
          'Inter',
          '"Helvetica Neue"',
          'sans-serif',
        ],
        mono: [
          '"SF Mono"',
          'Menlo',
          'Monaco',
          '"Cascadia Mono"',
          '"Roboto Mono"',
          'monospace',
        ],
      },
      letterSpacing: {
        'apple-display': '-0.022em',
        'apple-hero': '-0.028em',
        'apple-body': '-0.01em',
      },
      colors: {
        // Apple palette
        ink: {
          DEFAULT: '#1d1d1f',
          50: '#f5f5f7',
          100: '#ececee',
          200: '#d2d2d7',
          300: '#86868b',
          400: '#6e6e73',
          500: '#424245',
          600: '#2a2a2c',
          700: '#28282b',
          800: '#262629',
          900: '#1d1d1f',
          950: '#000000',
        },
        apple: {
          blue: '#0071e3',
          blueDark: '#0066cc',
          blueBright: '#2997ff',
          black: '#000000',
          graphite: '#1d1d1f',
          gray: '#f5f5f7',
        },
        // Semantic accents (kept narrow — Apple uses accent scarcely)
        emerald: {
          50: '#ecfdf5',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
        },
        amber: {
          500: '#f59e0b',
          600: '#d97706',
        },
        rose: {
          400: '#fb7185',
          500: '#f43f5e',
          600: '#e11d48',
        },
      },
      borderRadius: {
        'apple-sm': '5px',
        'apple': '12px',
        'apple-md': '18px',
        'apple-lg': '28px',
        'apple-xl': '36px',
        'apple-pill': '980px',
      },
      boxShadow: {
        'apple-sm': '0 1px 2px rgba(0,0,0,0.04), 0 1px 1px rgba(0,0,0,0.02)',
        'apple': '0 4px 16px rgba(0,0,0,0.08)',
        'apple-lg': '0 12px 40px rgba(0,0,0,0.12)',
        'apple-hi': '0 24px 60px rgba(0,0,0,0.22)',
      },
      backdropBlur: {
        apple: '22px',
      },
      transitionTimingFunction: {
        'apple': 'cubic-bezier(0.28, 0.11, 0.32, 1)',
      },
      animation: {
        'gradient-x': 'gradient-x 12s ease infinite',
        'fade-up': 'fade-up 600ms cubic-bezier(0.28, 0.11, 0.32, 1) both',
      },
      keyframes: {
        'gradient-x': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
export default config
