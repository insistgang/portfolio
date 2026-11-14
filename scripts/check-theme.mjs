import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

const code = readFileSync('assets/theme.js', 'utf8');
const themeKey = 'leo-portfolio-theme';
const styleKey = 'leo-portfolio-style';
const styles = ['finance', 'blue', 'paper'];
const pageColors = {
  finance: { light: '248 250 252', dark: '15 24 27' },
  blue: { light: '241 245 253', dark: '13 22 41' },
  paper: { light: '247 243 235', dark: '31 26 22' }
};

export function checkThemeMarkup(html, page) {
  const scriptAt = html.indexOf('assets/theme.js');
  assert.ok(scriptAt > 0 && scriptAt < html.indexOf('rel="stylesheet"'), `${page} 需在样式加载前应用主题`);
  assert.ok(html.includes('assets/theme.css') && html.includes('data-appearance-controls'), `${page} 缺少共享外观控件`);
  assert.ok(!/data-theme-select|<select[^>]*aria-label="外观主题"/.test(html), `${page} 不得恢复主题下拉菜单`);
  assert.equal([...html.matchAll(/<button[^>]*data-theme-toggle\b/g)].length, 1, `${page} 需要一个直接切换日夜的按钮`);
  assert.ok(html.includes('class="theme-sun"') && html.includes('class="theme-moon"'), `${page} 需包含太阳和月亮图标`);
  assert.ok(html.includes('aria-label="切换到夜间模式"') && html.includes('aria-label="视觉风格"'), `${page} 缺少外观控件可访问名称`);
  const options = [...html.matchAll(/<button[^>]*data-style-option="([^"]+)"[^>]*>/g)];
  assert.deepEqual(options.map(match => match[1]), styles, `${page} 风格选项不一致`);
  for (const option of options) assert.ok(/aria-pressed="(true|false)"/.test(option[0]), `${page} 风格按钮缺少选中状态`);
}

function boot({ storedTheme = null, storedStyle = null, dark = false, blocked = false, writeBlocked = false } = {}) {
  const values = new Map([[themeKey, storedTheme], [styleKey, storedStyle]].filter(([, value]) => value !== null));
  const documentEvents = {}, windowEvents = {};
  const button = (dataset = {}, toggle = false) => ({
    dataset, attributes: {}, title: '',
    hasAttribute: name => toggle && name === 'data-theme-toggle',
    setAttribute(name, value) { this.attributes[name] = value; }
  });
  const toggle = button({}, true);
  const choices = styles.map(style => button({ styleOption: style }));
  const control = { hidden: true };
  const root = { dataset: {} };
  const meta = { content: '#f8fafc' };
  let ready = false;
  let mediaChange;
  const system = { matches: dark, addEventListener(_event, listener) { mediaChange = listener; } };
  const localStorage = {
    getItem(name) { if (blocked) throw Error('SecurityError'); return values.get(name) ?? null; },
    setItem(name, value) { if (blocked || writeBlocked) throw Error('QuotaExceededError'); values.set(name, value); }
  };
  const changes = [];
  const window = {
    matchMedia: () => system,
    addEventListener(event, listener) { windowEvents[event] = listener; },
    dispatchEvent(event) { changes.push(event.detail); }
  };
  const document = {
    documentElement: root,
    querySelector: () => meta,
    querySelectorAll(selector) {
      if (!ready) return [];
      if (selector === '[data-theme-toggle]') return [toggle];
      if (selector === '[data-style-option]') return choices;
      if (selector === '[data-appearance-controls]') return [control];
      throw Error(`Unexpected selector: ${selector}`);
    },
    addEventListener(event, listener) { documentEvents[event] = listener; }
  };
  const getComputedStyle = () => ({ getPropertyValue: () => ready ? pageColors[root.dataset.style][root.dataset.theme] : '' });
  runInNewContext(code, { window, document, localStorage, getComputedStyle, CustomEvent: class { constructor(type, init) { this.type = type; this.detail = init.detail; } } });
  const click = target => documentEvents.click({ target: { closest: () => target } });
  return {
    root, meta, toggle, choices, control, values, changes,
    ready() { ready = true; documentEvents.DOMContentLoaded(); },
    clickToggle() { click(toggle); },
    chooseStyle(value) { click(choices.find(choice => choice.dataset.styleOption === value) || button({ styleOption: value })); },
    clickOutside() { click(null); },
    system(darkMode) { system.matches = darkMode; mediaChange(); },
    storage(key, newValue) { windowEvents.storage({ key, newValue }); }
  };
}

for (const dark of [false, true]) {
  const app = boot({ dark });
  assert.equal(app.root.dataset.theme, dark ? 'dark' : 'light', '首屏应同步系统主题，不等待 DOM 完成');
  assert.equal(app.root.dataset.style, 'finance', '默认采用财务看板风格');
  app.ready();
  assert.equal(app.control.hidden, false);
  assert.equal(app.toggle.attributes['aria-label'], dark ? '切换到日间模式' : '切换到夜间模式');
  app.system(!dark);
  assert.equal(app.root.dataset.theme, dark ? 'light' : 'dark', '未手动选择时继续跟随系统');
  app.clickToggle();
  assert.equal(app.root.dataset.theme, dark ? 'dark' : 'light', '一次点击直接切换，不能循环第三种模式');
  assert.equal(app.values.get(themeKey), app.root.dataset.theme);
  app.system(dark);
  app.system(!dark);
  assert.equal(app.root.dataset.theme, dark ? 'dark' : 'light', '手动选择不得被系统覆盖');
  app.chooseStyle('paper');
  assert.equal(app.root.dataset.style, 'paper');
  assert.equal(app.root.dataset.theme, dark ? 'dark' : 'light', '切换风格不应改变日夜偏好');
  assert.equal(app.values.get(styleKey), 'paper');
  assert.deepEqual(app.choices.map(choice => choice.attributes['aria-pressed']), ['false', 'false', 'true']);
  const restored = boot({ storedTheme: app.values.get(themeKey), storedStyle: app.values.get(styleKey) });
  assert.equal(restored.root.dataset.theme, app.root.dataset.theme);
  assert.equal(restored.root.dataset.style, 'paper');
  app.storage(styleKey, 'blue');
  assert.equal(app.root.dataset.style, 'blue');
  assert.equal(app.root.dataset.theme, dark ? 'dark' : 'light', '跨页签风格同步不应覆盖日夜设置');
  app.storage(themeKey, 'dark');
  assert.equal(app.root.dataset.style, 'blue');
  assert.equal(app.root.dataset.theme, 'dark');
  assert.equal(app.toggle.title, '切换到日间模式');
  app.storage('unrelated-key', 'light');
  assert.equal(app.root.dataset.theme, 'dark', '不得响应其他项目设置');
  app.chooseStyle('invalid');
  assert.equal(app.root.dataset.style, 'blue', '忽略未知按钮选项');
  const count = app.changes.length;
  app.clickOutside();
  assert.equal(app.changes.length, count, '普通点击不得触发主题重绘');
  app.storage(styleKey, null);
  assert.equal(app.root.dataset.style, 'finance');
  assert.equal(app.root.dataset.theme, 'dark');
  app.chooseStyle('paper');
  app.storage(null, null);
  assert.equal(app.root.dataset.style, 'finance');
  assert.equal(app.root.dataset.themePreference, 'system', '清空存储后恢复系统模式');
  assert.ok(app.changes.every(change => styles.includes(change.style) && ['dark', 'light'].includes(change.theme)));
}
for (const style of styles) {
  for (const theme of ['light', 'dark']) {
    const app = boot({ storedStyle: style, storedTheme: theme });
    app.ready();
    assert.equal(app.root.dataset.style, style);
    assert.equal(app.root.dataset.theme, theme, '兼容上一版已保存的日夜选择');
    assert.equal(app.meta.content, `rgb(${pageColors[style][theme]})`);
    app.clickToggle();
    app.clickToggle();
    assert.equal(app.root.dataset.theme, theme);
    assert.equal(app.root.dataset.style, style);
  }
}
for (const value of ['', 'auto', '{broken', null]) {
  const app = boot({ storedTheme: value, storedStyle: value, dark: true });
  assert.equal(app.root.dataset.theme, 'dark', '未知主题设置应回退系统');
  assert.equal(app.root.dataset.style, 'finance', '未知风格应回退财务绿');
}
for (const options of [{ blocked: true }, { writeBlocked: true }]) {
  const app = boot(options);
  app.ready();
  app.clickToggle();
  app.chooseStyle('blue');
  assert.equal(app.root.dataset.theme, 'dark', '拒绝存储时日夜切换仍应有效');
  assert.equal(app.root.dataset.style, 'blue', '拒绝存储时风格选择仍应有效');
}
console.log('通过：太阳／月亮直切、三套风格、首屏与旧设置恢复、独立持久化、系统变化、跨页签及存储异常回归。');
