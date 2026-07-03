export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],
  theme: {
    extend: {
      colors: {
        border: '#e2e8f0',
        input: '#e2e8f0',
        ring: '#2563eb',
        background: '#f6f8fb',
        foreground: '#0f172a',
        primary: { DEFAULT: '#020617', foreground: '#ffffff' },
        secondary: { DEFAULT: '#f8fafc', foreground: '#334155' },
        muted: { DEFAULT: '#f1f5f9', foreground: '#64748b' },
        destructive: { DEFAULT: '#dc2626', foreground: '#ffffff' },
        audit: { ink: '#16202a', muted: '#64748b', line: '#d8dee6', panel: '#f7f9fb', accent: '#0f766e' }
      },
      borderRadius: { lg: '8px', md: '6px', sm: '4px' },
      boxShadow: { soft: '0 1px 2px rgba(15,23,42,.05)' }
    }
  },
  plugins: []
};
