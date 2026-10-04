import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { Script } from 'node:vm';

const html = readFileSync('index.html', 'utf8');
const projects = JSON.parse(html.match(/const projects\s*=\s*(\[[\s\S]*?\n\]);/)[1]);
const awards = html.slice(html.indexOf('<section id="awards"'), html.indexOf('<section id="research"'));
for (const project of projects.filter(p => p.category === 'competition')) {
  assert.ok(awards.includes(project.title), `证书墙与项目标题不一致：${project.id}`);
  assert.ok(awards.includes(project.image), `证书墙与项目配图不一致：${project.id}`);
}
assert.equal(new Set(projects.map(p => p.id)).size, projects.length, '项目 ID 必须唯一');
assert.equal(projects.filter(p => p.category === 'softcopy').length, 14);
assert.ok(projects.filter(p => p.category === 'softcopy').every(p => p.status === '已提交申请'), '提交不等于登记获证');
assert.ok(!/\/Users\/|100%可申报|191张图|成功涨薪|线下碰面/.test(html), '公开页面不得包含内部路径或过时过程信息');
for (const script of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) {
  new Script(script[1]);
}
const assets = new Set(projects.flatMap(p => [p.image, ...(p.gallery || []), ...(p.url?.startsWith('assets/') ? [p.url] : [])]));
for (const match of html.matchAll(/(?:src|href)="(assets\/[^"$]+)"/g)) assets.add(match[1]);
for (const asset of assets) assert.ok(existsSync(asset), `资源缺失：${asset}`);
for (const match of html.matchAll(/openModal\('([^']+)'\)/g)) {
  assert.ok(projects.some(p => p.id === match[1]), `详情入口不存在：${match[1]}`);
}
assert.ok(!/<script[^>]+src="https?:|@import url\('https?:/.test(html), '运行时脚本与字体不得依赖外部 CDN');
assert.ok(html.includes('aria-label="搜索作品"'));
assert.ok(html.includes('role="dialog"'));
console.log(`通过：${projects.length} 条展示记录、14 项申请状态、${assets.size} 个资源、脚本语法与公开内容检查。`);
