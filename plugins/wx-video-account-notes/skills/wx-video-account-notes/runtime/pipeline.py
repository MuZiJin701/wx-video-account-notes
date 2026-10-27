from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Sequence

from runtime.archive import write_archive
from runtime.resolve_link import resolve_share_link
from runtime.download_video import download_file
from runtime.media_extract import extract_ocr_frames, extract_visual_frames, extract_audio
from runtime.ocr_runner import run_ocr
from runtime.asr_runner import resolve_asr_model_dir, run_asr
from runtime.compose_note import build_note_materials
from runtime.platform import find_ffmpeg_tools, runtime_root


def slugify(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value.strip())
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    if len(cleaned) > 80:
        suffix = hashlib.sha1(cleaned.encode("utf-8")).hexdigest()[:8]
        cleaned = f"{cleaned[:71].rstrip('_')}_{suffix}"
    if cleaned.upper() in {"CON", "PRN", "AUX", "NUL", *(f"{p}{n}" for p in ("COM", "LPT") for n in range(1, 10))}:
        cleaned = "_" + cleaned
    return cleaned or "wx_channels_video"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--share-url", required=True)
    parser.add_argument("--output-dir")
    args = parser.parse_args(argv)
    skill_root = Path(args.skill_root).resolve()
    runtime_path = runtime_root(skill_root)
    resolved = resolve_share_link(args.share_url)
    slug = slugify(resolved.get("title") or resolved.get("author") or "wx_channels_video")
    parent = Path(args.output_dir).resolve() if args.output_dir else Path.cwd().resolve()
    parent.mkdir(parents=True, exist_ok=True)
    for number in range(1, 1_000_000):
        output_dir = parent / (slug if number == 1 else f"{slug}_{number}")
        try:
            output_dir.mkdir()
            break
        except FileExistsError:
            continue
    else:
        raise RuntimeError("无法创建独立输出目录")
    print(f"[pipeline] output: {output_dir}")
    for name in ("images", "frames", "ocr_frames", "audio"):
        (output_dir / name).mkdir()
    (output_dir / "raw.json").write_text(resolved["raw_text"], encoding="utf-8")

    media: list[dict] = []
    errors: list[str] = []
    def save(label: str, kind: str, url: str, destination: Path) -> Path | None:
        item = {"label": label, "kind": kind, "path": None}
        media.append(item)
        try:
            path = download_file(url, destination, kind=kind)
            if kind in ("video", "audio"):
                try:
                    _, probe = find_ffmpeg_tools(runtime_path)
                    stream = "v:0" if kind == "video" else "a:0"
                    result = subprocess.run([str(probe), "-v", "error", "-select_streams", stream, "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(path)], capture_output=True, text=True, timeout=60)
                    if result.returncode or not result.stdout.strip():
                        raise ValueError("媒体流无法识别")
                except Exception:
                    path.unlink(missing_ok=True)
                    raise
            item["path"] = path
            return path
        except Exception as exc:
            cause = exc.__cause__ or exc
            known_errors = {"媒体地址不是受支持的腾讯 HTTPS 地址", "媒体文件不完整", "媒体格式不受支持或无法识别", "媒体重定向次数过多", "媒体流无法识别"}
            reason = str(cause) if isinstance(cause, ValueError) and str(cause) in known_errors else "网络请求或媒体校验失败"
            errors.append(f"{label}下载失败：{reason}")
            print(f"[pipeline] {label}下载失败：{reason}")
            return None

    video_path = None
    ffmpeg_path = ffprobe_path = None
    video_urls = resolved.get("video_urls") or ([resolved["video_url"]] if resolved.get("video_url") else [])
    for index, url in enumerate(video_urls):
        video_path = save("视频", "video", url, output_dir / slug)
        if video_path:
            ffmpeg_path, ffprobe_path = find_ffmpeg_tools(runtime_path)
            break
        if index + 1 < len(video_urls):
            media.pop()
            errors.pop()
    image_paths = []
    for index, url in enumerate(resolved.get("image_urls") or [], 1):
        path = save(f"图片 {index:03d}", "image", url, output_dir / "images" / f"{index:03d}")
        if path:
            image_paths.append(path)
    if resolved.get("cover_url"):
        cover_path = save("封面", "image", resolved["cover_url"], output_dir / "cover")
        if cover_path and not resolved.get("video_url") and not image_paths:
            image_paths.append(cover_path)
    bgm_urls = resolved.get("bgm_urls") or []
    if bgm_urls:
        # Alternative URLs describe the same background music; try each until one works.
        for url in bgm_urls:
            path = save("背景音乐", "audio", url, output_dir / "background_music")
            if path:
                break
            if url != bgm_urls[-1]:
                media.pop()
                errors.pop()

    is_video = resolved.get("media_type", "video") == "video"
    visual_frame_paths = list(image_paths)
    ocr_frame_paths = list(image_paths)
    ocr_error = ""
    audio_error = "图文动态无音频" if not is_video else "视频下载失败"
    if is_video and video_path:
        try:
            ocr_frame_paths = extract_ocr_frames(ffmpeg_path, ffprobe_path, video_path, output_dir / "ocr_frames")
        except Exception as exc:
            ocr_error = str(exc)
        try:
            visual_frame_paths = extract_visual_frames(ffmpeg_path, ffprobe_path, video_path, output_dir / "frames") + image_paths
        except Exception as exc:
            errors.append("视频参考帧提取失败")
        try:
            audio_path = extract_audio(ffmpeg_path, video_path, output_dir / "audio")
            audio_error = ""
        except Exception as exc:
            audio_error = str(exc)
    elif is_video:
        ocr_error = "视频下载失败"

    ocr_text = ""
    if ocr_frame_paths and not ocr_error:
        try:
            ocr_text = run_ocr(ocr_frame_paths, frames_are_subtitle_crops=is_video and bool(video_path))
            if not ocr_text.strip():
                ocr_error = "OCR produced no text"
        except Exception as exc:
            ocr_error = str(exc)
    elif not ocr_error:
        ocr_error = "没有可用图片"
    if is_video and image_paths:
        try:
            image_text = run_ocr(image_paths, frames_are_subtitle_crops=False)
            ocr_text = "\n".join(text for text in (ocr_text, image_text) if text)
        except Exception:
            errors.append("正文配图 OCR 失败")
    asr_text = ""
    if not audio_error:
        try:
            asr_text = run_asr(audio_path, resolve_asr_model_dir(runtime_path, "faster-whisper"))
            if not asr_text.strip():
                audio_error = "ASR produced no text"
        except Exception as exc:
            audio_error = str(exc)
    (output_dir / "ocr.txt").write_text(ocr_text, encoding="utf-8")
    (output_dir / "asr.txt").write_text(asr_text, encoding="utf-8")
    materials = build_note_materials(share_url=args.share_url, slug=slug, metadata=resolved, ocr_text=ocr_text,
                                     asr_text=asr_text, ocr_error=ocr_error, asr_error=audio_error,
                                     frame_paths=visual_frame_paths)
    materials["status"]["download"] = "; ".join(errors) if errors else "成功"
    (output_dir / "note_materials.json").write_text(json.dumps(materials, ensure_ascii=False, indent=2), encoding="utf-8")
    write_archive(output_dir, resolved, media, errors)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
