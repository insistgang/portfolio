#!/usr/bin/env python3
"""Generate the public career workflow page from the Career-Copilot master profile.

Usage:
    python3 scripts/build_career_page.py \
        --profile-dir "/path/to/Career-Copilot/data/master_profile" \
        --applications "/path/to/Career-Copilot/data/applications.json" \
        --resume "中文简历:/path/to/resume.pdf" \
        --resume "English resume:/path/to/resume_en.pdf" \
        --out career/index.html

The master profile is YAML; it is converted to JSON with the system Ruby YAML
parser so the repository keeps zero runtime dependencies.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
from pathlib import Path

STAGE_LABELS = {
    "todo": "准备投递",
    "applied": "已投递",
    "offer": "已接受实习 Offer",
    "screening": "初筛中",
    "interview": "面试中",
    "rejected": "已结束",
    "withdrawn": "已撤回",
}


def load_profile_yaml(path: Path) -> dict:
    script = (
        "d = YAML.safe_load(File.read(ARGV[0]), aliases: true); "
        "print(JSON.generate(d))"
    )
    result = subprocess.run(
        ["ruby", "-ryaml", "-rjson", "-e", script, str(path)],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def clean_md(value: str) -> str:
    value = re.sub(r"\*\*(.+?)\*\*", r"\1", str(value))
    value = re.sub(r"\s*/\s*软件著作权人", "", value)
    return value.strip()


def parse_project(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    title = ""
    meta: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("# ") and not title:
            title = clean_md(line[2:].strip())
            continue
        match = re.match(r"^-\s+\*\*(.+?)\*\*：(.+)$", line.strip())
        if match:
            meta[match.group(1).strip()] = clean_md(match.group(2).strip().strip("`"))

    tags = []
    raw_tags = meta.get("标签", "")
    if raw_tags:
        tags = [t.strip() for t in raw_tags.strip("[]").split(",") if t.strip()]

    challenge = ""
    section = re.search(r"##\s*[^#\n]*背景与挑战\s*\n(.*?)(?:\n---|\n##\s+[^#])", text, re.S)
    if section:
        for paragraph in section.group(1).split("\n"):
            paragraph = clean_md(paragraph.strip())
            if paragraph and not paragraph.startswith("#"):
                challenge = paragraph
                break

    highlights: list[str] = []
    body = re.search(r"##\s*多维度描述[^\n]*\n(.*?)(?:\n##\s+[^#]|\Z)", text, re.S)
    if body:
        for line in body.group(1).splitlines():
            line = clean_md(line.strip())
            if line.startswith("- ") and len(line) > 12:
                highlights.append(line[2:].strip())
            if len(highlights) == 2:
                break

    return {
        "title": title,
        "meta": meta,
        "tags": tags,
        "challenge": challenge,
        "highlights": highlights,
    }


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)



TARGET_GROUPS = {"all": "全部", "active": "Offer / 初筛中 / 面试中", "sent": "已投递", "prep": "准备中 / 待确认", "closed": "已结束"}


def application_stage(item: dict) -> tuple[str, str, str]:
    status = str(item.get("status", "")).lower()
    stage = str(item.get("stage") or STAGE_LABELS.get(status, status) or "待确认")
    if re.search(r"拒绝|未通过|不通过|已结束|撤回|放弃|终止|不合适", stage) or status in {"rejected", "withdrawn", "closed"}:
        return "closed", "prep", stage
    if re.search(r"offer", stage, re.I) or status == "offer":
        return "active", "offer", stage
    if re.search(r"初筛|筛选.*进行中|面试|复试|笔试", stage) or status in {"screening", "interview"}:
        return "active", "screen", stage
    if re.search(r"已投递|已发送", stage) or status == "applied":
        return "sent", "sent", stage
    return "prep", "prep", stage


def render_targets(applications: list[dict]) -> str:
    counts = {group: 0 for group in TARGET_GROUPS}
    rows = []
    for item in applications:
        group, badge, stage = application_stage(item)
        counts[group] += 1
        rows.append(f'''        <tr data-group="{group}">
          <td>{esc(item.get("company", ""))}</td>
          <td>{esc(item.get("position", ""))}</td>
          <td><span class="stage-badge stage-{badge}">{esc(stage)}</span></td>
          <td>{esc(item.get("channel") or "—")}</td>
          <td class="font-mono text-xs">{esc(item.get("deadline") or "—")}</td>
        </tr>''')
    counts["all"] = len(applications)
    filters = []
    for group, label in TARGET_GROUPS.items():
        if group == "closed" and not counts[group]:
            continue
        active = group == "all"
        filters.append(f'''      <button type="button" class="filter-pill{' active' if active else ''}" data-stage="{group}" aria-pressed="{str(active).lower()}" onclick="filterTargets('{group}')">{label} ({counts[group]})</button>''')
    return f'''<section class="page-wrap pb-16" aria-labelledby="targets-title">
  <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-5">
    <div>
      <h2 id="targets-title" class="section-title mb-2">目标岗位与投递进展</h2>
      <p id="targets-summary" class="text-sm text-slate-400" aria-live="polite">共 {len(applications)} 条记录</p>
    </div>
    <div class="flex flex-wrap gap-2" role="group" aria-label="按投递阶段筛选">
{chr(10).join(filters)}
    </div>
  </div>
  <div class="panel overflow-x-auto">
    <table class="w-full text-sm">
      <thead><tr><th>单位</th><th>岗位</th><th>阶段</th><th>渠道</th><th>时间节点</th></tr></thead>
      <tbody id="targets-tbody">
{chr(10).join(rows)}
      </tbody>
    </table>
  </div>
</section>'''


TARGET_SCRIPT = """  <script>
    function filterTargets(group) {
      const rows = [...document.querySelectorAll('#targets-tbody tr')];
      let visible = 0;
      rows.forEach(row => {
        const show = group === 'all' || row.dataset.group === group;
        row.style.display = show ? '' : 'none';
        if (show) visible += 1;
      });
      document.querySelectorAll('.filter-pill').forEach(btn => {
        const active = btn.dataset.stage === group;
        btn.classList.toggle('active', active);
        btn.setAttribute('aria-pressed', String(active));
      });
      const summary = document.getElementById('targets-summary');
      if (summary) summary.textContent = `显示 ${visible} / ${rows.length} 条投递记录`;
    }
    filterTargets('all');
  </script>"""


def build(data: dict, applications: list[dict], resumes: list[tuple[str, str]]) -> str:
    info = data.get("basic_info", {})
    skills = data.get("skills", {})
    awards = data.get("awards", {})
    education = data.get("education", [])
    projects = data.get("projects", [])
    internships = data.get("internships", [])
    ip = data.get("publications_and_ip", {})

    parts: list[str] = []
    add = parts.append

    add('<!DOCTYPE html>\n<html lang="zh-CN">\n<head>')
    add('  <meta charset="UTF-8">')
    add('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    add(f'  <title>{esc(info.get("name", ""))} {esc(info.get("english_name", ""))} · 求职工作流与经历主库</title>')
    add(f'  <meta name="description" content="{esc(info.get("name", ""))}的求职工作流与经历主库：{esc(info.get("title", ""))}，含 {len(projects)} 个核心项目、奖项、实习与目标岗位投递进展。">')
    add('  <meta name="theme-color" content="#141719">')
    add('  <link rel="canonical" href="https://insistgang.top/portfolio/career/">')
    add('  <link rel="icon" href="../assets/brand/favicon.ico" sizes="16x16 32x32 48x48">')
    add('  <link rel="icon" type="image/svg+xml" href="../assets/brand/leo-mark.svg" sizes="any">')
    add('  <link rel="stylesheet" href="../assets/site.css">')
    add(STYLE)
    add('</head>')
    add('<body class="bg-slate-950 text-slate-100 min-h-screen antialiased">')
    add(HEADER)
    add('<main>')

    add('<section class="hero">')
    add('  <div class="page-wrap">')
    add(f'    <p class="hero-kicker">CAREER WORKFLOW · {esc(info.get("title", ""))}</p>')
    add(f'    <h1 class="hero-title">{esc(info.get("name", ""))} <span class="hero-en">{esc(info.get("english_name", ""))}</span></h1>')
    add(f'    <p class="hero-lead">{esc(info.get("summary", ""))}</p>')
    if resumes:
        add('    <div class="flex flex-wrap gap-3 mt-6">')
        for label, href in resumes:
            add(f'      <a class="download-btn" href="{esc(href)}" download>{esc(label)} ↓</a>')
        add('    </div>')
    add('    <dl class="contact-grid">')
    for label, key in (("电话", "phone"), ("邮箱", "email"), ("微信", "wechat"), ("城市", "location")):
        value = info.get(key)
        if not value:
            continue
        if key == "email":
            add(f'      <div><dt>{label}</dt><dd><a href="mailto:{esc(value)}">{esc(value)}</a></dd></div>')
        elif key == "phone":
            add(f'      <div><dt>{label}</dt><dd>{esc(value)}</dd></div>')
        else:
            add(f'      <div><dt>{label}</dt><dd>{esc(value)}</dd></div>')
    for label, key in (("GitHub", "github"), ("博客", "blog"), ("作品集", "portfolio")):
        value = info.get(key)
        if value:
            add(f'      <div><dt>{label}</dt><dd><a class="link-accent" href="{esc(value)}" target="_blank" rel="noopener noreferrer">{esc(value)}</a></dd></div>')
    add('    </dl>')
    add('  </div>')
    add('</section>')

    if education:
        add('<section class="page-wrap pb-16" aria-labelledby="edu-title">')
        add('  <h2 id="edu-title" class="section-title">教育背景</h2>')
        add('  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">')
        for item in education:
            add('    <article class="panel p-6">')
            add(f'      <h3 class="font-medium mb-1">{esc(item.get("school", ""))} · {esc(item.get("college", ""))}</h3>')
            add(f'      <p class="text-sm text-slate-400 mb-2">{esc(item.get("degree", ""))} · {esc(item.get("period", ""))}</p>')
            if item.get("gpa"):
                add(f'      <p class="text-sm text-slate-400 mb-2">GPA {esc(item["gpa"])}</p>')
            if item.get("advisor"):
                add(f'      <p class="text-sm text-slate-400 mb-2">导师：{esc(item["advisor"])}</p>')
            if item.get("thesis_title"):
                add(f'      <p class="text-sm text-slate-400 mb-3">论文：{esc(item["thesis_title"])}</p>')
            for honor in item.get("honors", []) or []:
                add(f'      <p class="text-sm text-slate-300 leading-6">· {esc(honor)}</p>')
            add('    </article>')
        add('  </div>')
        add('</section>')

    if skills:
        add('<section class="page-wrap pb-16" aria-labelledby="skills-title">')
        add('  <h2 id="skills-title" class="section-title">核心能力</h2>')
        add('  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">')
        for key, group in skills.items():
            if key == "inference_and_deployment":
                group = {**group, "description": "实践 Qwen 模型量化、QLoRA 微调和 ONNX / TensorRT 部署，探索单卡离线推理与 Jetson 端侧部署；具体性能以可复现测试为准。"}
            add('    <article class="panel p-6">')
            add(f'      <h3 class="font-medium mb-2">{esc(group.get("title", ""))}</h3>')
            add(f'      <p class="text-sm leading-7 text-slate-400 mb-4">{esc(group.get("description", ""))}</p>')
            tags = group.get("tags", []) or []
            add('      <div class="flex flex-wrap gap-2">')
            for tag in tags:
                add(f'        <span class="tag px-3 py-1 text-xs">{esc(tag)}</span>')
            add('      </div>')
            add('    </article>')
        add('  </div>')
        add('</section>')

    if projects:
        add('<section class="page-wrap pb-16" aria-labelledby="projects-title">')
        add(f'  <h2 id="projects-title" class="section-title">核心项目证据库（{len(projects)}）</h2>')
        add('  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">')
        for project in projects:
            if "understand_mov_v2" in project.get("title", ""):
                project = {**project, "challenge": "针对无声录屏缺少可检索索引的问题，结合 FFmpeg 抽帧、多模态分析与 SQLite FTS5 全文检索定位画面。", "highlights": ["使用 SQLite 持久化任务队列，支持重启恢复、分阶段处理和失败重试。", "公开页面为静态演示；真实处理需启动后端并配置模型服务。"], "tags": ["FastAPI", "React", "FFmpeg", "SQLite FTS5"]}
            meta = project.get("meta", {})
            add('    <article class="panel p-6">')
            add(f'      <h3 class="font-medium mb-2">{esc(project.get("title", ""))}</h3>')
            facts = [meta.get(key) for key in ("时间", "角色", "机构", "竞赛", "荣誉") if meta.get(key)]
            if facts:
                add(f'      <p class="text-xs text-slate-500 mb-3">{esc(" · ".join(facts))}</p>')
            if project.get("challenge"):
                add(f'      <p class="text-sm leading-7 text-slate-400 mb-3">{esc(project["challenge"])}</p>')
            for highlight in project.get("highlights", []):
                add(f'      <p class="text-sm leading-6 text-slate-300 mb-2">· {esc(highlight)}</p>')
            if project.get("tags"):
                add('      <div class="flex flex-wrap gap-2 mt-3">')
                for tag in project["tags"]:
                    add(f'        <span class="tag px-2 py-0.5 text-[11px]">{esc(tag)}</span>')
                add('      </div>')
            add('    </article>')
        add('  </div>')
        add('</section>')

    if internships:
        add('<section class="page-wrap pb-16" aria-labelledby="intern-title">')
        add('  <h2 id="intern-title" class="section-title">实习与工作</h2>')
        add('  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">')
        for item in internships:
            add('    <article class="panel p-6">')
            add(f'      <h3 class="font-medium mb-1">{esc(item.get("company", ""))}</h3>')
            add(f'      <p class="text-sm text-slate-400 mb-2">{esc(item.get("role", ""))} · {esc(item.get("period", ""))}</p>')
            if item.get("description"):
                add(f'      <p class="text-sm leading-7 text-slate-400 mb-3">{esc(item["description"])}</p>')
            if item.get("tags"):
                add('      <div class="flex flex-wrap gap-2">')
                for tag in item["tags"]:
                    add(f'        <span class="tag px-2 py-0.5 text-[11px]">{esc(tag)}</span>')
                add('      </div>')
            add('    </article>')
        add('  </div>')
        add('</section>')

    national = awards.get("national", []) or []
    provincial = awards.get("provincial", []) or []
    university = awards.get("university", []) or []
    if national or provincial or university:
        add('<section class="page-wrap pb-16" aria-labelledby="awards-title">')
        add('  <h2 id="awards-title" class="section-title">竞赛与荣誉</h2>')
        for heading, rows in (("国家级", national), ("省部级", provincial), ("校级", university)):
            if not rows:
                continue
            add(f'    <h3 class="sub-title">{heading}</h3>')
            add('    <ul class="award-list">')
            for row in rows:
                extra = f'（{esc(row["role"])}）' if row.get("role") else ""
                add(f'      <li><span class="award-level">{esc(row.get("level", ""))}</span> {esc(row.get("name", ""))}{extra} · {esc(row.get("year", ""))}</li>')
            add('    </ul>')
        papers = ip.get("papers", []) or []
        if papers:
            add('    <h3 class="sub-title">学位论文与代表性研究</h3>')
            add('    <ul class="award-list">')
            for paper in papers:
                role = f'（{esc(paper["role"])}）' if paper.get("role") else ""
                add(f'      <li>{esc(paper.get("title", ""))}{role} · {esc(paper.get("status", ""))}</li>')
            add('    </ul>')
        add('</section>')

    certifications = data.get("certifications", []) or []
    if certifications:
        add('<section class="page-wrap pb-16" aria-labelledby="cert-title">')
        add('  <h2 id="cert-title" class="section-title">专业能力认证</h2>')
        add('  <ul class="award-list">')
        for item in certifications:
            line = "".join(esc(part) for part in (item.get("name", ""), item.get("level", "")) if part)
            if item.get("date"):
                line += f"（{esc(item['date'])}）"
            if item.get("issuer"):
                line += f" · {esc(item['issuer'])}"
            add(f"      <li>{line}</li>")
        add('  </ul>')
        add('</section>')

    if applications:
        add(render_targets(applications))

    if resumes:
        add('<section class="page-wrap pb-16" aria-labelledby="resume-title">')
        add('  <h2 id="resume-title" class="section-title">简历下载</h2>')
        add('  <div class="flex flex-wrap gap-4">')
        for label, href in resumes:
            add(f'    <a class="download-btn" href="{esc(href)}" download>{esc(label)} ↓</a>')
        add('  </div>')
        add('</section>')

    add(SYSTEM_SECTION)
    add('</main>')
    add(FOOTER)
    add(TARGET_SCRIPT)
    add('</body>\n</html>')
    return "\n".join(parts)


STYLE = """  <style>
    :root {
      color-scheme: dark;
      --page: 20 23 25;
      --surface: 27 31 33;
      --surface-raised: 36 41 44;
      --line: 52 58 61;
      --copy: 238 234 224;
      --muted: 168 171 174;
      --accent: 186 208 218;
    }
    html { scroll-behavior: smooth; }
    body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; }
    .font-mono { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: rgb(var(--page)); }
    ::-webkit-scrollbar-thumb { background: rgb(var(--surface-raised)); border-radius: 4px; }
    .site-header { position: sticky; top: 0; z-index: 40; background: rgb(var(--page) / 0.92); backdrop-filter: blur(12px); border-bottom: 1px solid rgb(var(--line)); }
    .site-header-inner { width: min(100% - 64px, 1120px); margin: 0 auto; min-height: 64px; padding: 10px 0; display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
    .site-brand { display: inline-flex; align-items: center; color: #f0eee8; font-size: 16px; font-weight: 600; white-space: nowrap; text-decoration: none; }
    .site-mark { width: 28px; height: 28px; flex: none; margin-right: 10px; }
    .site-brand span { margin-left: 7px; color: #a8abae; font-family: Georgia, serif; font-style: italic; font-weight: 400; }
    .site-header a:hover { color: #fff; }
    .site-links { display: flex; align-items: center; gap: 16px; font-size: 13px; color: #b9bcbf; flex-wrap: wrap; }
    .site-links a { text-decoration: none; transition: color .15s ease; }
    .page-wrap { width: min(100% - 64px, 1120px); margin: 0 auto; }
    .hero { padding: 64px 0 40px; }
    .hero-kicker { margin: 0 0 14px; font-size: 12px; color: #9ec5db; letter-spacing: .14em; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
    .hero-title { margin: 0; font-size: 40px; line-height: 1.2; letter-spacing: -.03em; font-weight: 600; color: rgb(var(--copy)); }
    .hero-en { margin-left: 14px; font-family: Georgia, serif; font-style: italic; font-weight: 400; color: #a8abae; }
    .hero-lead { max-width: 820px; margin-top: 18px; color: #c5c8cb; font-size: 15px; line-height: 1.9; }
    .contact-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px 24px; margin: 28px 0 0; padding: 20px 24px; background: rgb(var(--surface)); border: 1px solid rgb(var(--line)); border-radius: 14px; }
    .contact-grid dt { font-size: 11px; color: #a8abae; letter-spacing: .08em; }
    .contact-grid dd { margin: 4px 0 0; font-size: 13.5px; color: rgb(var(--copy)); word-break: break-all; }
    .section-title { font-size: 1.6rem; font-weight: 600; letter-spacing: -.02em; margin-bottom: 20px; color: #f2efe9; }
    .sub-title { font-size: 12px; letter-spacing: .14em; color: #9ec5db; margin: 26px 0 10px; font-weight: 600; }
    .panel { background: rgb(var(--surface)); border: 1px solid rgb(var(--line)); border-radius: 14px; transition: border-color .2s ease; }
    .panel:hover { border-color: #4f5d65; }
    .tag { border: 1px solid rgb(var(--line)); background: rgb(var(--page) / 0.55); color: #ced2cf; border-radius: 6px; }
    .award-list { list-style: none; padding: 0; margin: 0; }
    .award-list li { padding: 11px 0; border-bottom: 1px solid rgb(var(--line)); font-size: 14px; color: #d8d8d3; display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px 12px; }
    .award-level { color: #e2c98d; font-weight: 600; min-width: 140px; }
    table { border-collapse: collapse; }
    th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid rgb(var(--line)); vertical-align: middle; }
    th { font-size: 11px; letter-spacing: .08em; color: #a8abae; font-weight: 600; background: rgb(var(--page) / 0.5); }
    td { font-size: 13px; color: #d0d2cf; }
    tbody tr:hover { background: rgb(var(--surface-raised) / 0.55); }
    .stage-badge { display: inline-flex; align-items: center; padding: 2px 9px; border-radius: 999px; font-size: 11.5px; font-weight: 500; border: 1px solid transparent; }
    .stage-offer { background: rgba(16, 185, 129, 0.14); color: #6ee7b7; border-color: rgba(16, 185, 129, 0.35); }
    .stage-screen { background: rgba(56, 189, 248, 0.14); color: #7dd3fc; border-color: rgba(56, 189, 248, 0.35); }
    .stage-sent { background: rgba(245, 158, 11, 0.12); color: #fcd34d; border-color: rgba(245, 158, 11, 0.3); }
    .stage-prep { background: rgba(148, 163, 184, 0.12); color: #cbd5e1; border-color: rgba(148, 163, 184, 0.25); }
    .filter-pill { padding: 6px 12px; border-radius: 8px; font-size: 12px; border: 1px solid rgb(var(--line)); background: rgb(var(--surface)); color: #b9bcbf; cursor: pointer; transition: all .15s ease; }
    .filter-pill:hover { color: #fff; border-color: #667d87; }
    .filter-pill.active { background: #dce8ee; color: #141719; border-color: #dce8ee; font-weight: 600; }
    .download-btn { display: inline-flex; align-items: center; gap: 8px; background: #eeeae0; color: #141719; border: 1px solid #eeeae0; border-radius: 8px; padding: 10px 18px; font-size: 13.5px; font-weight: 600; text-decoration: none; transition: all .15s ease; }
    .download-btn:hover { background: #fff; border-color: #fff; }
    .secondary-btn { display: inline-flex; align-items: center; gap: 8px; background: rgb(var(--surface)); color: #e5e7eb; border: 1px solid rgb(var(--line)); border-radius: 8px; padding: 10px 16px; font-size: 13.5px; font-weight: 500; text-decoration: none; transition: all .15s ease; }
    .secondary-btn:hover { border-color: #88a2ae; color: #fff; }
    a { color: inherit; }
    .link-accent { color: #bad0da; border-bottom: 1px solid #667d87; text-decoration: none; }
    .link-accent:hover { color: #fff; }
    :focus-visible { outline: 2px solid rgb(var(--accent)); outline-offset: 4px; }
    footer { border-top: 1px solid rgb(var(--line)); color: #a8abae; }
    @media (max-width: 640px) {
      .site-header-inner, .page-wrap { width: calc(100% - 32px); }
      .hero { padding: 40px 0 28px; }
      .hero-title { font-size: 28px; }
      .site-links { gap: 12px; font-size: 12px; }
      .award-level { min-width: auto; }
    }
  </style>"""

HEADER = """  <header class="site-header">
    <nav class="site-header-inner" aria-label="主导航">
      <a href="../" class="site-brand"><img src="../assets/brand/leo-mark.svg" class="site-mark" width="28" height="28" alt="">刘钢 <span>/ Leo · Career-Copilot</span></a>
      <div class="site-links">
        <a href="../">← 返回作品集</a>
        <a href="#edu-title">教育</a>
        <a href="#skills-title">核心能力</a>
        <a href="#projects-title">核心项目</a>
        <a href="#intern-title">实习经历</a>
        <a href="#awards-title">竞赛荣誉</a>
        <a href="#targets-title">投递进展</a>
        <a href="../yds/">视频大屏</a>
        <a href="https://insistgang.top/" target="_blank" rel="noopener noreferrer">博客 ↗</a>
      </div>
    </nav>
  </header>"""

SYSTEM_SECTION = """  <section class="page-wrap pb-20" aria-labelledby="system-title">
    <h2 id="system-title" class="section-title">这套页面背后的系统</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <article class="panel p-6">
        <h3 class="font-medium mb-3">五段链路</h3>
        <p class="text-sm leading-7 text-slate-300">
          经历证据 → 岗位匹配 → 简历生成 → 投递跟踪 → 邮件回执。同一份经历主库同时服务企业招聘与高校申请，
          所有外发主张均绑定真实证书、代码或交付记录，不编造指标与分工。
        </p>
      </article>
      <article class="panel p-6">
        <h3 class="font-medium mb-3">运行方式</h3>
        <p class="text-sm leading-7 text-slate-300">
          投递看板、邮箱读取与 Typst 简历编译在本机运行，接口受会话令牌保护；本页是经历主库的脱敏公开视图，
          随主库更新同步生成。
        </p>
      </article>
    </div>
    <div class="flex flex-wrap gap-3 mt-6">
      <span class="tag px-3 py-1 text-xs">Python</span>
      <span class="tag px-3 py-1 text-xs">Typst</span>
      <span class="tag px-3 py-1 text-xs">HTML / CSS</span>
      <span class="tag px-3 py-1 text-xs">MCP</span>
      <span class="tag px-3 py-1 text-xs">IMAP</span>
      <span class="tag px-3 py-1 text-xs">Markdown / YAML</span>
    </div>
  </section>"""

FOOTER = """  <footer class="page-wrap py-8 text-sm flex flex-wrap items-center justify-between gap-x-8 gap-y-3">
    <div class="flex flex-wrap items-center gap-x-6 gap-y-2">
      <a href="../" class="link-accent">← 返回作品集主站</a>
      <a href="../yds/" class="link-accent">LinkAble 视频数据大屏</a>
      <a href="https://insistgang.top/" target="_blank" rel="noopener noreferrer" class="link-accent">读我的博客 ↗</a>
      <a href="mailto:insistgang@163.com" class="link-accent">联系我 (insistgang@163.com)</a>
    </div>
    <span class="text-xs text-slate-500 font-mono">Career-Copilot Public Snapshot</span>
  </footer>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-dir", type=Path, required=True)
    parser.add_argument("--applications", type=Path, required=True)
    parser.add_argument("--resume", action="append", default=[], help="标签:相对或绝对路径")
    parser.add_argument("--out", type=Path, default=Path("career/index.html"))
    args = parser.parse_args()

    profile = load_profile_yaml(args.profile_dir / "profile.yaml")
    profile["projects"] = [
        parse_project(path) for path in sorted((args.profile_dir / "projects").glob("*.md"))
    ]
    applications = json.loads(args.applications.read_text(encoding="utf-8"))
    resumes = []
    for item in args.resume:
        label, _, target = item.partition(":")
        resumes.append((label, target))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build(profile, applications, resumes), encoding="utf-8")
    print(f"生成完成：{args.out}（项目 {len(profile['projects'])} 个，投递记录 {len(applications)} 条）")


if __name__ == "__main__":
    main()
