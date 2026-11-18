from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import quote


def write_archive(output_dir: Path, resolved: dict, media: list[dict], errors: list[str]) -> None:
    feed = resolved.get("feed_info") or {}
    details = []
    timestamp = feed.get("createtime")
    if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool):
        try:
            details.append("时间（UTC）：" + datetime.fromtimestamp(timestamp, timezone.utc).isoformat())
        except (ValueError, OverflowError, OSError):
            pass
    for key, label in (("likeCountFmt", "点赞"), ("favCountFmt", "收藏"), ("forwardCountFmt", "转发"), ("commentCountFmt", "评论")):
        if isinstance(feed.get(key), (str, int)):
            details.append(f"{label}：{feed[key]}（查询时展示值）")
    if isinstance(feed.get("jumpInfo"), dict) and isinstance(feed["jumpInfo"].get("wording"), str):
        details.append(feed["jumpInfo"]["wording"])
    entries = []
    for item in media:
        path = item.get("path")
        label = escape(item["label"])
        if not path:
            entries.append(f"<li>{label}：下载失败</li>")
            continue
        source = quote(Path(path).relative_to(output_dir).as_posix(), safe="/")
        kind = item["kind"]
        preview = f'<img src="{source}" alt="{label}" loading="lazy">' if kind == "image" else f'<{kind} src="{source}" controls preload="none"></{kind}>'
        entries.append(f'<li><h2>{label}</h2>{preview}<p><a href="{source}">打开文件</a></p></li>')
    state = "部分完成" if errors and any(item.get("path") for item in media) else "失败" if errors else "完成"
    information = "".join(f"<p>{escape(value)}</p>" for value in details)
    failures = "".join(f"<li>{escape(error)}</li>" for error in errors)
    title = escape(str(resolved.get("title") or "视频号动态"))
    author = escape(str(resolved.get("author") or "未知作者"))
    (output_dir / "index.html").write_text(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; media-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{title}</title><style>body{{max-width:64rem;margin:auto;padding:1.5rem;font-family:system-ui;overflow-wrap:anywhere}} .description{{white-space:pre-wrap}} img,video{{max-width:100%;max-height:75vh}} audio{{max-width:100%}} li{{margin:1em 0}}</style></head>
<body><h1>{title}</h1><p>{state}</p><p>作者：{author}</p><p class="description">{title}</p>{information}<ul>{failures}</ul><ul>{''.join(entries)}</ul><p><a href="raw.json">解析原始数据</a></p></body></html>''', encoding="utf-8")
