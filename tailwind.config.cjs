module.exports = {
  content: ['./index.html'],
  theme: {
    extend: {
      colors: {
        white: 'rgb(var(--copy) / <alpha-value>)',
        slate: {
          100: 'rgb(var(--copy) / <alpha-value>)',
          200: '#ddded8',
          300: '#c5c7c4',
          400: 'rgb(var(--muted) / <alpha-value>)',
          500: '#949da1',
          600: '#727c82',
          700: '#42484b',
          800: 'rgb(var(--surface-raised) / <alpha-value>)',
          900: 'rgb(var(--surface) / <alpha-value>)',
          950: 'rgb(var(--page) / <alpha-value>)'
        },
        sky: { 300: '#c0d2da', 400: 'rgb(var(--accent) / <alpha-value>)', 500: '#465a63', 600: '#526974' },
        amber: { 200: '#ded3b6', 300: '#d5c69e', 400: '#c6b88f', 500: '#9e875d' },
        purple: { 300: '#cbc7d7', 400: '#bbb4cf', 500: '#817793' },
        emerald: { 300: '#c1cdbf', 400: '#adbfae', 500: '#7a927c' }
      },
      borderRadius: { lg: '6px', xl: '6px', '2xl': '8px' },
      boxShadow: { lg: 'none', xl: 'none', '2xl': '0 20px 60px rgb(0 0 0 / .3)' }
    }
  },
  plugins: []
};
