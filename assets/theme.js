(() => {
  const themeKey = 'leo-portfolio-theme';
  const styleKey = 'leo-portfolio-style';
  const styles = ['finance', 'blue', 'paper'];
  const root = document.documentElement;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  const normalizeTheme = value => ['light', 'dark'].includes(value) ? value : 'system';
  const normalizeStyle = value => styles.includes(value) ? value : 'finance';
  let preference = 'system';
  let style = 'finance';
  try {
    preference = normalizeTheme(localStorage.getItem(themeKey));
    style = normalizeStyle(localStorage.getItem(styleKey));
  } catch { /* Storage can be disabled. */ }

  function apply() {
    const theme = preference === 'system' ? (system.matches ? 'dark' : 'light') : preference;
    root.dataset.theme = theme;
    root.dataset.themePreference = preference;
    root.dataset.style = style;
    const meta = document.querySelector('meta[name="theme-color"]');
    const pageColor = getComputedStyle(root).getPropertyValue('--page').trim();
    if (meta && pageColor) meta.content = `rgb(${pageColor})`;
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      const label = theme === 'dark' ? '切换到日间模式' : '切换到夜间模式';
      button.setAttribute('aria-label', label);
      button.title = label;
    });
    document.querySelectorAll('[data-style-option]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.styleOption === style));
    });
    window.dispatchEvent(new CustomEvent('portfolio:themechange', { detail: { theme, preference, style } }));
  }

  apply();
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-appearance-controls]').forEach(control => { control.hidden = false; });
    apply();
  });
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-theme-toggle], [data-style-option]');
    if (!button) return;
    if (button.hasAttribute('data-theme-toggle')) {
      preference = root.dataset.theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem(themeKey, preference); } catch { /* Keep the choice in memory. */ }
    } else {
      const value = button.dataset.styleOption;
      if (!styles.includes(value)) return;
      style = value;
      try { localStorage.setItem(styleKey, style); } catch { /* Keep the choice in memory. */ }
    }
    apply();
  });
  system.addEventListener('change', () => { if (preference === 'system') apply(); });
  window.addEventListener('storage', event => {
    if (![themeKey, styleKey, null].includes(event.key)) return;
    if (event.key === themeKey || event.key === null) preference = normalizeTheme(event.newValue);
    if (event.key === styleKey || event.key === null) style = normalizeStyle(event.newValue);
    apply();
  });
})();
