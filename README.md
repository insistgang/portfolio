# 刘钢 Leo · 软件工程与研究作品集

公开站点：[insistgang.top/portfolio](https://insistgang.top/portfolio/) 。
GitHub Pages 原始地址会跳转到该域名。部署来源为本仓库 `main` 分支根目录。

## 内容

当前版本收录 **40 条展示记录**：14 项软著申请、10 组竞赛记录、4 项研究工作、4 项产业实践和 8 项个人工具。
同一项目的软著、竞赛或工具成果可能分别展示，40 不是去重后的独立项目数。

14 项软著均为 V1.0，申请已提交由本人于 2026-10-04 确认；当前未展示为已获登记证书。
项目功能与技术栈依据最新提交材料和可用工程说明校正，详情配图来自对应材料；示例数值不作为实测指标。
新增工具为 Career-Copilot 和 PaperStudio，仅展示公开功能简介。

竞赛证书已补齐 2025 年西门子杯华北二赛区一等奖、2026 年西门子杯华东一赛区二等奖，以及 2026 年第二十一届研电赛上海分赛区团队二等奖。学生证书与教师证书、不同年度和不同赛区分别记录，不将初赛赛区奖项标为全国总决赛奖项。

共感 LinkAble 为 2026 两岸大学生创客大赛逢甲赛区／台湾交流项目，未获奖，以产品方案与交互原型收录。2026 年研电赛对应另一套边缘计算盒子，与同年西门子杯共用设备，分别面向辅助通行感知和工业预警场景。

内容依据和修订边界见 [CONTENT_NOTES.md](CONTENT_NOTES.md)，当前进度与待补信息见 [ROADMAP.md](ROADMAP.md)。

## 使用

网站运行时只需静态文件，无服务器应用、数据库或 Node.js 进程。可直接打开 `index.html`，或启动本机预览：

```bash
python3 -m http.server 8766 --bind 127.0.0.1
```

浏览器访问 `http://127.0.0.1:8766/`。支持五类作品筛选、名称/说明/技术栈/状态搜索、结果计数、键盘打开卡片与详情弹窗。

首屏采用左对齐个人介绍与 EdgeSafe 设备联调照片，项目数量和申请状态在作品库中展示。顶部导航及个人介绍下方均提供 [Leo 的笔记本](https://insistgang.top/) 博客入口，桌面与手机布局都可直接访问。

整页采用同一套炭灰背景、暖白文字、中性卡片与低饱和强调色。主题颜色由 `index.html` 中的 CSS 变量与 `tailwind.config.cjs` 的调色板统一维护，避免首屏、作品库、证书墙和弹窗出现不同底色。

## 维护与验证

样式和图标已随站点保存，不依赖运行时 CDN 或在线字体。使用现有 Tailwind 3 样式体系；锁定版本仅用于构建。

```bash
npm ci --ignore-scripts
npm run build
npm run check
```

修改页面或动态模板中的 CSS 类后重新构建。发布时包含 `index.html` 和其引用的 `assets/` 文件；`assets/site.css` 和 `assets/vendor/` 是需要随站点保存的正式静态资源。

- `index.html`：页面、项目数据与交互。
- `assets/images/`：项目配图；`soft/submitted-*.png` 为本次从提交材料提取的图。
- `assets/images/certs/cimc-2025-liugang.png`、`cimc-2026-liugang.png`：两届西门子杯原始学生证书图片。
- `assets/certificates/gedc-2026-edge-device.pdf`：研电赛原始 PDF；页面配图由该 PDF 渲染。
- `styles/input.css`、`tailwind.config.cjs`：样式构建入口。
- `scripts/vendor.mjs`：复制固定版本图标库及许可。
- `scripts/check.mjs`：校验项目 ID、申请状态、资源、详情入口、脚本语法和公开内容边界。
- `.tmp/`：本机预览与核验中间文件，不参与发布。

## 发布方式

本仓库已有 GitHub Pages 站点，可直接展示静态页面。若迁到阿里云，可用现有 Nginx 在 HTTPS 子域名下托管相同文件，无需新增应用端口。
访问者无需 GitHub 账户即可浏览公开页面；公开仓库链接用于进一步了解源码。正文不会嵌入私有求职看板、申请表或邮件材料。

## 第三方许可

Tailwind CSS 使用 MIT 许可，Lucide 使用 ISC 许可；对应许可随 `assets/vendor/` 分发。项目证书、截图及第三方标识不因网页公开而改变原有权属。
