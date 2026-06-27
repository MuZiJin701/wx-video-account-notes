from __future__ import annotations

import argparse
from pathlib import Path
import json
import time
from typing import Sequence

from runtime.resolve_link import resolve_share_link
from runtime.download_video import download_video, download_images
from runtime.media_extract import extract_ocr_frames, extract_visual_frames, extract_audio
from runtime.ocr_runner import run_ocr
from runtime.asr_runner import resolve_asr_model_dir, run_asr
from runtime.compose_note import build_note_materials


def slugify(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value.strip())
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned or "wx_channels_video"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--share-url", required=True)
    parser.add_argument("--output-dir")
    args = parser.parse_args(argv)

    skill_root = Path(args.skill_root).resolve()
    runtime_root = skill_root / ".runtime"

    resolved = resolve_share_link(args.share_url)
    title = resolved.get("title") or resolved.get("author") or "wx_channels_video"
    slug = slugify(title)

    output_dir = Path(args.output_dir).resolve() if args.output_dir else (Path.cwd() / slug).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "frames").mkdir(exist_ok=True)
    (output_dir / "ocr_frames").mkdir(exist_ok=True)
    (output_dir / "audio").mkdir(exist_ok=True)

    raw_json_path = output_dir / "raw.json"
    raw_json_path.write_text(resolved["raw_text"], encoding="utf-8")

    media_type = resolved.get("media_type") or "video"
    video_path = output_dir / f"{slug}.mp4"
    if media_type == "video":
        print("[pipeline] [1/5] downloading video ...")
        t0 = time.time()
        download_video(resolved["video_url"], video_path)
        print(f"[pipeline] [1/5] download done  ({time.time()-t0:.1f}s)")
    elif media_type == "image":
        print("[pipeline] [1/5] downloading images ...")
        t0 = time.time()
        visual_frame_paths = download_images(resolved.get("image_urls") or [], output_dir / "frames")
        print(f"[pipeline] [1/5] images done  ({time.time()-t0:.1f}s, {len(visual_frame_paths)} images)")
    else:
        raise RuntimeError(f"Unsupported media type: {media_type}")

    ocr_frames_error = ""
    if media_type == "video":
        ffmpeg_root = runtime_root / "tools" / "ffmpeg"
        try:
            ffmpeg_path = next(ffmpeg_root.glob("**/bin/ffmpeg.exe"))
            ffprobe_path = next(ffmpeg_root.glob("**/bin/ffprobe.exe"))
        except StopIteration:
            raise RuntimeError(
                "ffmpeg/ffprobe not found in .runtime/tools/ffmpeg/. "
                "Run scripts/bootstrap.ps1 first to download runtime assets."
            ) from None

        print("[pipeline] [2/5] extracting OCR and visual frames ...")
        t0 = time.time()
        try:
            ocr_frame_paths = extract_ocr_frames(ffmpeg_path, ffprobe_path, video_path, output_dir / "ocr_frames")
            print(f"[pipeline] [2/5] OCR frames done  ({time.time()-t0:.1f}s, {len(ocr_frame_paths)} frames)")
        except Exception as exc:
            ocr_frame_paths = []
            ocr_frames_error = str(exc)
            print(f"[pipeline] [2/5] OCR frames FAILED: {exc}")

        try:
            visual_frame_paths = extract_visual_frames(ffmpeg_path, ffprobe_path, video_path, output_dir / "frames")
            print(f"[pipeline] [2/5] visual frames done  ({time.time()-t0:.1f}s, {len(visual_frame_paths)} frames)")
        except Exception as exc:
            visual_frame_paths = []
            print(f"[pipeline] [2/5] visual frames FAILED: {exc}")
    else:
        print(f"[pipeline] [2/5] using {len(visual_frame_paths)} downloaded images as OCR/visual frames ...")
        ocr_frame_paths = visual_frame_paths

    audio_error = ""
    if media_type == "video":
        print("[pipeline] [3/5] extracting audio ...")
        t0 = time.time()
        try:
            audio_path = extract_audio(ffmpeg_path, video_path, output_dir / "audio")
            print(f"[pipeline] [3/5] audio done  ({time.time()-t0:.1f}s)")
        except Exception as exc:
            audio_path = output_dir / "audio" / "speech.wav"
            audio_error = str(exc)
            print(f"[pipeline] [3/5] audio FAILED: {exc}")
    else:
        audio_path = output_dir / "audio" / "speech.wav"
        audio_error = "图文动态无音频"
        print("[pipeline] [3/5] skipping audio for image feed")

    ocr_error = ocr_frames_error
    ocr_text = ""
    if not ocr_frames_error:
        ocr_input_label = "subtitle frames" if media_type == "video" else "images"
        print(f"[pipeline] [4/5] running OCR on {len(ocr_frame_paths)} {ocr_input_label} ...")
        t0 = time.time()
        try:
            ocr_text = run_ocr(ocr_frame_paths, frames_are_subtitle_crops=(media_type == "video"))
            if not ocr_text.strip():
                ocr_error = "OCR produced no text"
            print(f"[pipeline] [4/5] OCR done  ({time.time()-t0:.1f}s)")
        except Exception as exc:
            ocr_text = ""
            ocr_error = str(exc)
            print(f"[pipeline] [4/5] OCR FAILED: {exc}")
    (output_dir / "ocr.txt").write_text(ocr_text, encoding="utf-8")

    asr_error = audio_error
    asr_text = ""
    if not audio_error:
        print("[pipeline] [5/5] running ASR ...")
        t0 = time.time()
        try:
            model_path = resolve_asr_model_dir(runtime_root, "faster-whisper")
            asr_text = run_asr(audio_path, model_path)
            if not asr_text.strip():
                asr_error = "ASR produced no text"
            print(f"[pipeline] [5/5] ASR done  ({time.time()-t0:.1f}s)")
        except Exception as exc:
            asr_text = ""
            asr_error = str(exc)
            print(f"[pipeline] [5/5] ASR FAILED: {exc}")
    (output_dir / "asr.txt").write_text(asr_text, encoding="utf-8")

    materials = build_note_materials(
        share_url=args.share_url,
        slug=slug,
        metadata=resolved,
        ocr_text=ocr_text,
        asr_text=asr_text,
        ocr_error=ocr_error,
        asr_error=asr_error,
        frame_paths=visual_frame_paths,
    )
    (output_dir / "note_materials.json").write_text(
        json.dumps(materials, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
