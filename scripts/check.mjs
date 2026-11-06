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
const illustratedProjects = projects.filter(p => p.image);
assert.equal(new Set(illustratedProjects.map(p => p.image)).size, illustratedProjects.length, '有图项目的主封面图必须唯一');
assert.equal(Number(html.match(/data-count="all">(\d+)/)[1]), projects.length, '初始展示记录数必须与项目数据一致');
const productCount = html.match(/data-cat="products">\s*<span>[^<]+<\/span>\s*<span[^>]*>(\d+)<\/span>/);
assert.equal(Number(productCount?.[1]), projects.filter(p => p.category === 'products').length, '软件作品初始数量必须与项目数据一致');
for (const project of projects) {
  assert.ok(['competition', 'research', 'industry', 'products'].includes(project.category), `未知分类：${project.id}`);
  assert.ok(project.imageCaption && project.imageCaption.trim().length > 0, `缺少配图说明 imageCaption：${project.id}`);
  if (!project.image) {
    assert.equal(project.image, null, `无图项目必须显式标记 null：${project.id}`);
    assert.ok(project.imageUnavailableNote, `无图项目必须说明原因：${project.id}`);
    assert.ok(!project.gallery?.length, `无图项目不得残留未核验画廊：${project.id}`);
  }
  if (project.gallery) {
    assert.equal(project.gallery[0], project.image, `画廊首图须与封面一致：${project.id}`);
    assert.equal(project.gallery.length, project.galleryCaptions?.length, `每张画廊图片须有对应说明：${project.id}`);
  }
}
assert.ok(!projects.some(p => p.category === 'softcopy'), '作品集不再展示软著申请');
assert.ok(!/软著/.test(html), '公开页面不再出现软著');
assert.ok(!/\/Users\/|100%可申报|191张图|成功涨薪|线下碰面/.test(html), '公开页面不得包含内部路径或过时过程信息');
for (const script of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) {
  new Script(script[1]);
}
const assets = new Set(projects.flatMap(p => [p.image, ...(p.gallery || []), ...(p.url?.startsWith('assets/') ? [p.url] : [])]).filter(Boolean));
for (const match of html.matchAll(/(?:src|href)="(assets\/[^"$]+)"/g)) assets.add(match[1]);
for (const asset of assets) assert.ok(existsSync(asset), `资源缺失：${asset}`);
for (const match of html.matchAll(/openModal\('([^']+)'\)/g)) {
  assert.ok(projects.some(p => p.id === match[1]), `详情入口不存在：${match[1]}`);
}
for (const project of projects) {
  const links = project.links ?? (project.url ? [{ href: project.url, label: project.urlLabel }] : []);
  for (const link of links) {
    assert.ok(link.href && link.label, `链接缺少 href 或 label：${project.id}`);
    assert.ok(/^(https?:\/\/|mailto:|assets\/|career\/|yds\/)/.test(link.href), `链接协议非法：${project.id} → ${link.href}`);
    if (link.href.startsWith('assets/')) assert.ok(existsSync(link.href), `链接资源缺失：${project.id} → ${link.href}`);
    if (/^(career|yds)\/$/.test(link.href)) assert.ok(existsSync(`${link.href}index.html`), `子页面缺失：${project.id} → ${link.href}`);
  }
  if (project.privateNote) {
    assert.ok(!links.length, `私人使用范畴项目不应挂外链：${project.id}`);
    assert.ok(/私人使用范畴/.test(project.privateNote), `私人说明需标注「私人使用范畴」：${project.id}`);
  }
}
const projectById = Object.fromEntries(projects.map(project => [project.id, project]));
const featured = html.slice(html.indexOf('<section id="featured"'), html.indexOf('<section id="gallery"'));
const featuredIds = [...featured.matchAll(/data-featured-project="([^"]+)"/g)].map(match => match[1]);
assert.deepEqual(featuredIds, ['prod-17', 'prod-03', 'prod-20'], '精选案例顺序应为 Agent 安全、知识工作流、视频检索');
for (const id of featuredIds) {
  const project = projectById[id];
  const study = project.caseStudy;
  const article = featured.match(new RegExp(`<article id="case-${id}"[\\s\\S]*?</article>`))?.[0];
  assert.ok(article && study, `精选案例缺少记录或结构：${id}`);
  assert.ok(article.includes(project.title) && article.includes(project.image), `精选标题与配图需和记录一致：${id}`);
  for (const key of ['problem', 'responsibility', 'boundary']) {
    assert.ok(study[key]?.trim() && article.includes(study[key]), `精选正文与案例数据不一致：${id}/${key}`);
  }
  assert.ok(study.decisions.length >= 2 && study.evidence.length >= 2, `案例需包含技术取舍与证据：${id}`);
  for (const decision of study.decisions) assert.ok(article.includes(decision), `精选技术决策不同步：${id}`);
  for (const evidence of study.evidence) {
    assert.ok(/^https:\/\/github\.com\/insistgang\//.test(evidence.href), `案例证据应链接已核对仓库：${id}`);
    assert.ok(evidence.label && evidence.note && article.includes(evidence.href) && article.includes(evidence.note), `精选证据不同步：${id}`);
  }
  for (const field of ['problem', 'responsibility', 'decisions', 'evidence', 'boundary']) {
    assert.ok(article.includes(`data-case-field="${field}"`), `精选案例缺少内容层次：${id}/${field}`);
  }
}
assert.ok(featured.includes('https://insistgang.top/LinkLab/') && featured.includes('href="yds/"') && featured.includes("openModal('prod-01')"), '精选重组不得丢失互助应用、边缘大屏与总台入口');
assert.ok(html.includes('${caseHtml}'), '详情弹窗需展示案例内容');
const contentOf = id => JSON.stringify(projectById[id]);
const imageSources = JSON.parse(readFileSync('assets/images/screenshots/sources.json', 'utf8'));
for (const [id, entry] of Object.entries(imageSources)) {
  assert.equal(projectById[id]?.image, entry.image, `封面与来源记录不一致：${id}`);
  assert.ok(entry.source && entry.capturedAt && entry.kind === 'screenshot', `截图来源记录不完整：${id}`);
}
for (const project of projects) {
  if (project.image?.startsWith('assets/images/screenshots/')) assert.ok(imageSources[project.id], `缺少截图来源：${project.id}`);
  if (project.category === 'products' && project.image) assert.ok(!project.image.endsWith('.svg'), `产品封面应使用核验截图，不使用自绘占位图：${project.id}`);
}
assert.equal(projectById['comp-04'].gallery[1], 'assets/images/soft/submitted-05.png', 'AI 竞赛必须对应语文学习系统原图');
assert.equal(projectById['comp-05'].gallery[1], 'assets/images/soft/submitted-06.png', '网安竞赛必须对应告警研判工作区原图');
assert.ok(!projects.some(p => p.gallery?.includes('assets/images/certs/cert_ximengzi.jpg')), '不得将教师证书作为个人或团队证书使用');
assert.ok(!projects.some(p => p.id !== 'prod-01' && p.gallery?.includes('assets/images/soft/submitted-14.png')), '不得将 Ops-Hub 架构图用于其他项目');

assert.ok(!/不可篡改/.test(contentOf('prod-17')), 'AEGIS 不得将审计留痕表述为不可篡改');
assert.ok(/SQLite/.test(contentOf('prod-17')), 'AEGIS 需说明审计存储实现');
assert.ok(!/毫秒级/.test(projectById['prod-20'].metrics), '视频检索不得展示未经基准验证的性能');
assert.ok(/持久化任务队列/.test(contentOf('prod-20')) && /重启恢复/.test(contentOf('prod-20')), '视频检索需区分任务处理能力与静态演示');
assert.ok(/家宴/.test(contentOf('prod-16')) && /吹哨/.test(contentOf('prod-16')), '食安崇明需使用实际业务主线');
assert.ok(/真实性及脱敏完整性未核实/.test(contentOf('prod-16')), '食安崇明不得将入口授权等同于示例数据核验');
assert.ok(/历史协作版/.test(contentOf('prod-05')) && /不自动跨设备同步/.test(contentOf('prod-05')), '体重管理需区分历史协作版与当前本机版');
assert.ok(/AI 首轮阅读稿/.test(contentOf('prod-14')) && /人工复核/.test(contentOf('prod-14')), '论文阅读库需区分 AI 阅读稿与人工复核');
assert.ok(/LangGraph/.test(contentOf('prod-03')) && /人工兜底/.test(contentOf('prod-03')), '知识库需说明工作流与人工兜底');
assert.ok(/本地 JSON/.test(contentOf('prod-15')) && /轮换备份/.test(contentOf('prod-15')), 'VitaFlow 需说明本地同步与备份');
assert.ok(/WORK\/LIFE/.test(contentOf('prod-21')) && /Git 同步回执不等同于 Pages 部署成功/.test(contentOf('prod-21')), '每日词汇需说明场景资料与发布边界');
assert.ok(!/<script[^>]+src="https?:|@import url\('https?:/.test(html), '运行时脚本与字体不得依赖外部 CDN');
assert.ok(html.includes('aria-label="搜索作品"'));
assert.ok(html.includes('role="dialog"'));

// Sub-page checks: career/index.html & yds/index.html
const careerHtml = readFileSync('career/index.html', 'utf8');
assert.ok(!/\*\*/.test(careerHtml), 'career/index.html 不得残留未解析的 Markdown 粗体符号 **');
assert.ok(!/软著|\/Users\//.test(careerHtml), 'career/index.html 不得包含软著或内部路径');
for (const match of careerHtml.matchAll(/(?:src|href)="\.\.\/(assets\/[^"$]+)"/g)) {
  assert.ok(existsSync(match[1]), `career/index.html 引用资源缺失：${match[1]}`);
}
for (const script of careerHtml.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) {
  new Script(script[1]);
}

const ydsHtml = readFileSync('yds/index.html', 'utf8');
assert.ok(ydsHtml.includes('<title>LinkAble 本地视频数据大屏</title>'), 'yds/index.html 需保持标题一致');
assert.ok(!/\/Users\//.test(ydsHtml), 'yds/index.html 不得包含内部路径');
for (const match of ydsHtml.matchAll(/(?:src|href)="\.\.\/(assets\/[^"$]+)"/g)) {
  assert.ok(existsSync(match[1]), `yds/index.html 引用资源缺失：${match[1]}`);
}
for (const match of ydsHtml.matchAll(/<script(?:\s+([^>]*))?>([\s\S]*?)<\/script>/g)) {
  const attrs = match[1] || '';
  if (attrs.includes('application/json')) {
    JSON.parse(match[2]);
  } else {
    new Script(match[2]);
  }
}

const pdfScript = readFileSync('scripts/build_portfolio_pdf.py', 'utf8');
for (const match of pdfScript.matchAll(/'(assets\/[^']+)'/g)) {
  assert.ok(existsSync(match[1]), `build_portfolio_pdf.py 引用资源缺失：${match[1]}`);
}
for (const match of pdfScript.matchAll(/'((?:comp|res|ind|prod)-\d+)'/g)) {
  assert.ok(projects.some(p => p.id === match[1]), `build_portfolio_pdf.py 引用项目 ID 不存在：${match[1]}`);
}

console.log(`通过：${projects.length} 条展示记录、${assets.size} 个主站资源、子页面（career/ 与 yds/）、PDF 构建脚本、脚本语法与公开内容检查。`);
