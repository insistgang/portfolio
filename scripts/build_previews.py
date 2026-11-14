#!/usr/bin/env python3
"""Generate lossy WebP thumbnails while keeping original evidence files untouched.

Requires Pillow. Run from the repository root:
    python3 scripts/build_previews.py
    python3 scripts/build_previews.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "assets/images/previews/sources.json"
MIN_SOURCE_BYTES = 100_000
MAX_SIDE = 1200


def source_images() -> set[str]:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    projects = json.JSONDecoder().raw_decode(html.split("const projects = ", 1)[1])[0]
    sources = {project["image"] for project in projects if project.get("image")}
    sources.update(re.findall(r'src="(assets/images/[^"$]+\.(?:png|jpe?g))"', html, re.I))
    for preview in re.findall(r'src="(assets/images/previews/[^"$]+\.webp)"', html, re.I):
        # Preview filenames retain the full original relative path, including its extension.
        relative = Path(preview).name.removesuffix(".webp").replace("__", "/")
        sources.add(f"assets/images/{relative}")
    return {
        source for source in sources
        if (ROOT / source).is_file() and (ROOT / source).stat().st_size >= MIN_SOURCE_BYTES
    }


def preview_path(source: str) -> str:
    relative = Path(source).relative_to("assets/images")
    return f"assets/images/previews/{str(relative).replace('/', '__')}.webp"


def generate(check: bool = False) -> None:
    existing = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    expected = {}
    for source in sorted(source_images()):
        original = ROOT / source
        data = original.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        preview = preview_path(source)
        output = ROOT / preview
        if not check:
            with Image.open(original) as image:
                image = ImageOps.exif_transpose(image)
                image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
                if image.mode not in {"RGB", "RGBA"}:
                    image = image.convert("RGBA")
                output.parent.mkdir(parents=True, exist_ok=True)
                image.save(output, "WEBP", quality=82, method=6)
        with Image.open(output) as image:
            image.load()
            assert image.width <= MAX_SIDE and image.height <= MAX_SIDE, f"预览尺寸超限：{preview}"
        assert output.stat().st_size < len(data), f"预览未减小文件：{preview}"
        expected[source] = {
            "image": preview,
            "originalSha256": digest,
            "originalBytes": len(data),
            "previewBytes": output.stat().st_size,
            "kind": "derivative-preview",
        }
    if check:
        assert expected == existing, "预览清单或内容过期，请运行 python3 scripts/build_previews.py"
        print(f"通过：{len(expected)} 张 WebP 预览均可解码、尺寸合规且与原图匹配。")
    else:
        MANIFEST.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        original_bytes = sum(item["originalBytes"] for item in expected.values())
        preview_bytes = sum(item["previewBytes"] for item in expected.values())
        print(f"已生成 {len(expected)} 张预览：{original_bytes / 1024 / 1024:.2f} MiB → {preview_bytes / 1024 / 1024:.2f} MiB；原图未修改。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(args.check)
