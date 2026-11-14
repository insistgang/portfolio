module.exports = {
  content: ['./index.html', './career/**/*.html', './yds/**/*.html'],
  theme: {
    extend: {
      colors: {
        white: 'rgb(var(--copy) / <alpha-value>)',
        slate: {
          100: 'rgb(var(--copy) / <alpha-value>)',
          200: 'rgb(var(--copy-soft) / <alpha-value>)',
          300: 'rgb(var(--secondary) / <alpha-value>)',
          400: 'rgb(var(--muted) / <alpha-value>)',
          500: 'rgb(var(--muted) / <alpha-value>)',
          600: 'rgb(var(--line-strong) / <alpha-value>)',
          700: 'rgb(var(--line-strong) / <alpha-value>)',
          800: 'rgb(var(--surface-raised) / <alpha-value>)',
          900: 'rgb(var(--surface) / <alpha-value>)',
          950: 'rgb(var(--page) / <alpha-value>)'
        },
        sky: Object.fromEntries([300, 400, 500, 600].map(step => [step, 'rgb(var(--accent) / <alpha-value>)'])),
        amber: Object.fromEntries([200, 300, 400, 500].map(step => [step, 'rgb(var(--amber) / <alpha-value>)'])),
        purple: Object.fromEntries([300, 400, 500].map(step => [step, 'rgb(var(--purple) / <alpha-value>)'])),
        emerald: Object.fromEntries([300, 400, 500].map(step => [step, 'rgb(var(--emerald) / <alpha-value>)']))
      },
      borderColor: { slate: { 800: 'rgb(var(--line) / <alpha-value>)', 700: 'rgb(var(--line-strong) / <alpha-value>)' } },
      borderRadius: { lg: '8px', xl: '12px', '2xl': '16px' },
      boxShadow: { lg: 'none', xl: 'none', '2xl': '0 20px 60px rgb(0 0 0 / .3)' }
    }
  },
  plugins: []
};
