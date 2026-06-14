from __future__ import annotations


def _is_noise_line(line: str) -> bool:
    if len(line) < 4:
        return True

    repeated_chunks = [
        "她是男生",
        "男生的男生",
    ]
    if any(chunk in line for chunk in repeated_chunks):
        return True

    return False


def _clean_lines(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("## ")]
    deduped: list[str] = []
    for line in lines:
        if _is_noise_line(line):
            continue
        if line not in deduped:
            deduped.append(line)
    return deduped


def _build_overview(metadata: dict, ocr_lines: list[str], asr_lines: list[str]) -> list[str]:
    overview: list[str] = []
    title = metadata.get("title")
    if title:
        overview.append(f"视频主题聚焦于：{title}")
    if ocr_lines:
        overview.append(f"画面文字主要强调：{ocr_lines[0]}")
    if asr_lines:
        overview.append(f"口播核心信息包括：{asr_lines[0]}")
    if not overview:
        overview.append("当前仅拿到有限元数据，无法生成更丰富的内容概览。")
    return overview


def _title_tags(title: str) -> list[str]:
    tags = []
    if "#" in title:
        for part in title.split("#"):
            cleaned = part.strip()
            if cleaned and cleaned != title.strip() and cleaned not in tags:
                tags.append(cleaned)
    return tags[:3]


def _build_summary(metadata: dict, ocr_lines: list[str], asr_lines: list[str]) -> list[str]:
    title = metadata.get("title") or "该视频"
    title_without_tags = title.split("#")[0].strip() or title

    summary = [f"视频主线：{title_without_tags}。"]
    if asr_lines:
        summary.append(f"从口播来看，关键情节包括：{asr_lines[0]}。")
        if len(asr_lines) > 1:
            summary.append(f"后续信息进一步提到：{asr_lines[1]}。")
    elif ocr_lines:
        summary.append(f"当前主要依据画面文字判断，核心线索是：{ocr_lines[0]}。")

    if ocr_lines:
        summary.append(f"画面字幕补充了这些信息：{'；'.join(ocr_lines[:2])}。")

    tags = _title_tags(title)
    if tags:
        summary.append(f"内容标签可归纳为：{'、'.join(tags)}。")

    return summary[:4]


def build_note_materials(
    *,
    share_url: str,
    slug: str,
    metadata: dict,
    ocr_text: str,
    asr_text: str,
    ocr_error: str,
    asr_error: str,
    frame_paths: list | None = None,
) -> dict:
    title = metadata.get("title") or slug
    author = metadata.get("author") or "未知"

    ocr_lines = _clean_lines(ocr_text)
    asr_lines = _clean_lines(asr_text)
    overview_lines = _build_overview(metadata, ocr_lines, asr_lines)
    summary_lines = _build_summary(metadata, ocr_lines, asr_lines)
    reusable_lines = asr_lines if asr_lines else ocr_lines

    visual_frames: list[str] = []
    if frame_paths and (not asr_lines or sum(len(line) for line in asr_lines) < 50):
        step = max(1, len(frame_paths) // 5)
        selected = frame_paths[::step][:5]
        visual_frames = [str(p) for p in selected]

    result: dict = {
        "share_url": share_url,
        "slug": slug,
        "metadata": {
            "title": title,
            "author": author,
            "raw_title": metadata.get("title") or "",
        },
        "ocr_lines": ocr_lines,
        "asr_lines": asr_lines,
        "overview_lines": overview_lines,
        "summary_lines": summary_lines,
        "reusable_lines": reusable_lines,
        "status": {
            "ocr": ocr_error or "成功",
            "asr": asr_error or "成功",
        },
    }
    if visual_frames:
        result["visual_frames"] = visual_frames
    return result


def _join_markdown_lines(lines: list[str]) -> str:
    if not lines:
        return "暂无内容。"

    paragraphs: list[str] = []
    step = 2
    for index in range(0, len(lines), step):
        paragraphs.append("；".join(lines[index:index + step]))
    return "\n\n".join(paragraphs)


def synthesize_markdown(materials: dict) -> str:
    metadata = materials["metadata"]
    title = metadata["title"]
    author = metadata.get("author") or "未知"
    share_url = materials["share_url"]
    summary_lines = materials.get("summary_lines") or materials.get("overview_lines") or []
    ocr_lines = materials.get("ocr_lines") or []
    reusable_lines = materials.get("reusable_lines") or materials.get("asr_lines") or ocr_lines
    status = materials.get("status") or {}

    summary = "\n".join(f"- {line}" for line in summary_lines) or "- 暂无可用梗概。"
    extracted_copy = _join_markdown_lines(ocr_lines)
    rewritten_copy = _join_markdown_lines(reusable_lines)
    ocr_status = status.get("ocr", "成功")
    asr_status = status.get("asr", "成功")

    return f"""# {title}

- 作者：{author}
- 原始链接：{share_url}

## 内容梗概

来源：原始元数据与提取内容整理

{summary}

## 提取到的文案

{extracted_copy}

## 转写文案

这份转写文案基于提取内容重新顺写，更便于继续设计文案稿子。

{rewritten_copy}

## 提取状态

- OCR：{ocr_status}
- ASR：{asr_status}
"""
