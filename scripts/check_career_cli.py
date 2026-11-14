"""Exercise the real career-page CLI with synthetic, non-private fixtures."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
(ROOT / ".tmp").mkdir(exist_ok=True)

with tempfile.TemporaryDirectory(prefix="career-cli-", dir=ROOT / ".tmp") as directory:
    work = Path(directory)
    projects = work / "projects"
    projects.mkdir()
    for index in range(15):
        title = "项目 07：understand_mov_v2" if index == 0 else f"项目 {index:02d}"
        (projects / f"{index:02d}.md").write_text(
            f"# {title}\n- **时间**：2026\n- **标签**：Python\n\n## 背景与挑战\n示例问题\n\n## 多维度描述\n- 示例实现与验证说明。\n",
            encoding="utf-8",
        )
    profile = {
        "basic_info": {"name": "Review", "summary": "国家级竞赛奖项 4 项、省部级奖项 6 项", "github": "https://example.com"},
        "education": [], "skills": {}, "internships": [], "awards": {"university": []},
    }
    (work / "profile.yaml").write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
    applications = [{"company": "Example", "position": "Engineer", "status": "offer" if index == 0 else "todo"} for index in range(29)]
    (work / "applications.json").write_text(json.dumps(applications), encoding="utf-8")
    assets = work / "assets/career"
    assets.mkdir(parents=True)
    for name in ("resume_zh_reviewed.pdf", "resume_en_reviewed.pdf"):
        shutil.copyfile(ROOT / "assets/career" / name, assets / name)
    output = work / "career/index.html"
    result = subprocess.run([
        "python3", "-B", str(ROOT / "scripts/build_career_page.py"),
        "--profile-dir", str(work), "--applications", str(work / "applications.json"),
        "--resume", "中文简历:assets/career/resume_zh_reviewed.pdf",
        "--resume", "English Resume:assets/career/resume_en_reviewed.pdf",
        "--out", str(output),
    ], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    page = output.read_text(encoding="utf-8")
    assert "核心项目证据库（15）" in page
    assert "Offer</span>" in page and "已接受实习 Offer" not in page
    assert "/Users/" not in page and "毫秒级" not in page
    assert "国家级竞赛奖项 4 项、省市与赛区奖项 7 项" in page
    profile["basic_info"]["github"] = "javascript:alert(1)"
    (work / "profile.yaml").write_text(json.dumps(profile), encoding="utf-8")
    rejected = work / "career/rejected.html"
    result = subprocess.run([
        "python3", "-B", str(ROOT / "scripts/build_career_page.py"),
        "--profile-dir", str(work), "--applications", str(work / "applications.json"),
        "--resume", "简历:/Users/example/private/resume.pdf", "--out", str(rejected),
    ], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode != 0 and not rejected.exists()
    assert "/Users/example/private/resume.pdf" not in result.stdout
print("通过：真实 CLI 的 YAML／Markdown 解析、15 个项目、29 条投递、Offer 标签、公开简历路径和错误输入拒绝。")
