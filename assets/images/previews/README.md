# 页面轻量预览

本目录存放页面卡片和静态展示使用的 WebP 缩略图，不是独立的项目证据。

- 原图仍保存在原路径；详情、高清原图链接和 PDF 生成器继续使用原件。
- `sources.json` 记录原图 SHA-256、原图与预览的字节数及预览路径，不使用原图之外的界面或数据。
- 只处理主站引用的较大 PNG / JPEG，最长边不超过 1200px，保留透明通道，移除预览副本的元数据。
- 原图更新后运行 `python3 scripts/build_previews.py`，再运行 `python3 scripts/build_previews.py --check`。脚本需要 Pillow；检查会验证原图摘要、文件大小和解码结果。
- `index.html` 的 `image` 字段保留证据原件，`preview` 字段只用于作品卡片；新增大图时需要同步预览清单。
