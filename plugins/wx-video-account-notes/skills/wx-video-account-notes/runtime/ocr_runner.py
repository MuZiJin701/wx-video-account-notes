from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


def _prepare_crop_candidates() -> list[tuple[float, float, float, float]]:
    return [
        (0.03, 0.5, 0.97, 1.0),
        (0.08, 0.62, 0.92, 0.96),
        (0.12, 0.66, 0.88, 0.94),
    ]


def _prepare_precropped_subtitle_candidates() -> list[tuple[float, float, float, float]]:
    return [
        (0.0, 0.0, 1.0, 1.0),
        (0.03, 0.1, 0.97, 1.0),
        (0.08, 0.25, 0.92, 1.0),
    ]


def _calculate_binarize_threshold(values: Iterable[int]) -> int:
    histogram = [0] * 256
    total = 0
    pixel_sum = 0
    for value in values:
        bucket = max(0, min(255, int(value)))
        histogram[bucket] += 1
        total += 1
        pixel_sum += bucket

    if total == 0:
        return 150

    midpoint = total // 2
    seen = 0
    median = 0
    for value, count in enumerate(histogram):
        seen += count
        if seen > midpoint:
            median = value
            break
    average = pixel_sum / total
    threshold = int((median * 0.6) + (average * 0.4))
    return max(80, min(210, threshold))


def _image_pixels(image) -> list[int]:
    pixel_source = getattr(image, "get_flattened_data", None)
    if pixel_source is None:
        pixel_source = image.getdata
    return list(pixel_source())


def _image_signature(image, size: tuple[int, int] = (16, 16)) -> tuple[int, ...]:
    grayscale = image.convert("L")
    reduced = grayscale.resize(size)
    return tuple(_image_pixels(reduced))


def _signature_changed(
    prev_signature: tuple[int, ...] | None,
    curr_signature: tuple[int, ...],
    threshold: float = 42.0,
) -> bool:
    if prev_signature is None:
        return True
    if len(prev_signature) != len(curr_signature):
        return True
    if not curr_signature:
        return False
    diff = sum(abs(prev - curr) for prev, curr in zip(prev_signature, curr_signature))
    return (diff / len(curr_signature)) > threshold


def _prepare_subtitle_crop(image, crop: tuple[float, float, float, float], upscale_factor: float = 1.5):
    from PIL import Image as PILImage

    width, height = image.size
    left_ratio, top_ratio, right_ratio, bottom_ratio = crop
    crop_box = (
        int(width * left_ratio),
        int(height * top_ratio),
        int(width * right_ratio),
        int(height * bottom_ratio),
    )
    cropped = image.crop(crop_box).convert("L")
    enlarged = cropped.resize((int(cropped.width * upscale_factor), int(cropped.height * upscale_factor)))
    threshold = _calculate_binarize_threshold(_image_pixels(enlarged))
    return PILImage.eval(enlarged, lambda value: 255 if value > threshold else 0)


def _prepare_subtitle_image(image, upscale_factor: float = 1.5):
    from PIL import Image as PILImage

    grayscale = image.convert("L")
    enlarged = grayscale.resize((int(grayscale.width * upscale_factor), int(grayscale.height * upscale_factor)))
    threshold = _calculate_binarize_threshold(_image_pixels(enlarged))
    return PILImage.eval(enlarged, lambda value: 255 if value > threshold else 0)


def _extract_text_lines(result: list | None) -> list[str]:
    if not result:
        return []
    return [item[1].strip() for item in result if len(item) > 1 and item[1].strip()]


def _looks_like_repeated_fragment(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) <= 4 and len(set(stripped)) == 1 and len(stripped) > 1:
        if len(stripped) == 2 and all("\u4e00" <= char <= "\u9fff" for char in stripped):
            return False
        return True
    midpoint = len(stripped) // 2
    if (
        len(stripped) >= 4
        and len(stripped) % 2 == 0
        and stripped == stripped[:midpoint] * 2
    ):
        return True
    return False


def _looks_like_watermark(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if len(stripped) == 1 and not (stripped.isalnum() or ("\u4e00" <= stripped <= "\u9fff")):
        return True
    punctuation_count = sum(
        1
        for char in stripped
        if not char.isalnum() and not ("\u4e00" <= char <= "\u9fff")
    )
    if len(stripped) <= 3 and punctuation_count <= 1 and any("\u4e00" <= char <= "\u9fff" for char in stripped):
        return False
    return punctuation_count / len(stripped) > 0.4


def _filter_ocr_lines(lines: list[str]) -> list[str]:
    filtered: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _looks_like_repeated_fragment(stripped):
            continue
        if _looks_like_watermark(stripped):
            continue
        filtered.append(stripped)
    return filtered


def _score_ocr_result(lines: list[str]) -> tuple[int, int, int, int]:
    filtered = _filter_ocr_lines(lines)
    text = "".join(filtered)
    chinese_count = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    digit_count = sum(1 for char in text if char.isdigit())
    longest_line_length = max((len(line) for line in filtered), default=0)
    return (chinese_count, len(text), longest_line_length, -digit_count)


def _add_scores(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return tuple(l + r for l, r in zip(left, right))


def _is_good_crop_result(lines: list[str], min_chinese_chars: int = 4) -> bool:
    chinese_count = sum(1 for char in "".join(lines) if "\u4e00" <= char <= "\u9fff")
    return chinese_count >= min_chinese_chars


def _is_poor_crop_result(lines: list[str]) -> bool:
    chinese_count = sum(1 for char in "".join(lines) if "\u4e00" <= char <= "\u9fff")
    return chinese_count == 0


def _fuse_frame_results(frame_results: list[list[str]]) -> list[str]:
    fused: list[str] = []
    for lines in frame_results:
        if not lines:
            continue
        overlap = 0
        max_overlap = min(len(fused), len(lines), 3)
        for candidate in range(max_overlap, 0, -1):
            if fused[-candidate:] == lines[:candidate]:
                overlap = candidate
                break
        fused.extend(lines[overlap:])
    return fused


def _decode_frame_image(frame_path: Path):
    from PIL import Image as PILImage

    return PILImage.open(frame_path).copy()


def _subtitle_region_pixels(image, crop: tuple[float, float, float, float]) -> list[int]:
    width, height = image.size
    crop_box = (
        int(width * crop[0]),
        int(height * crop[1]),
        int(width * crop[2]),
        int(height * crop[3]),
    )
    region = image.crop(crop_box).convert("L")
    return _image_pixels(region)


def _pixels_changed(
    prev_pixels: list[int] | None,
    curr_pixels: list[int],
    threshold: float = 0.02,
    pixel_diff_cutoff: int = 40,
) -> bool:
    if prev_pixels is None:
        return True
    if len(prev_pixels) != len(curr_pixels):
        return True
    diff = sum(1 for p, c in zip(prev_pixels, curr_pixels) if abs(p - c) > pixel_diff_cutoff)
    return diff / len(curr_pixels) > threshold


def run_ocr(
    frame_paths: list[Path],
    *,
    frames_are_subtitle_crops: bool = False,
    calibration_frame_count: int = 3,
) -> str:
    if not frame_paths:
        return ""

    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    frame_groups: list[list[str]] = []
    crops = _prepare_crop_candidates()
    subtitle_crops = _prepare_precropped_subtitle_candidates()

    prev_pixels: list[int] | None = None
    prev_signature: tuple[int, ...] | None = None
    prev_lines: list[str] = []
    selected_subtitle_crop: tuple[float, float, float, float] | None = None
    calibration_scores = [(0, 0, 0, 0) for _ in subtitle_crops]
    calibrated_frames = 0

    for frame_path in frame_paths:
        frame_image = _decode_frame_image(frame_path)

        if frames_are_subtitle_crops:
            curr_signature = _image_signature(frame_image)
            if not _signature_changed(prev_signature, curr_signature) and prev_lines:
                frame_groups.append(prev_lines)
                continue
        else:
            curr_pixels = _subtitle_region_pixels(frame_image, crops[0])
            if not _pixels_changed(prev_pixels, curr_pixels) and prev_lines:
                frame_groups.append(prev_lines)
                continue

        candidate_results: list[list[str]] = []
        got_good_crop = frames_are_subtitle_crops
        if frames_are_subtitle_crops:
            if selected_subtitle_crop is None:
                for candidate_index, crop in enumerate(subtitle_crops):
                    prepared = _prepare_subtitle_crop(frame_image, crop)
                    result, _ = engine(prepared)
                    lines = _filter_ocr_lines(_extract_text_lines(result))
                    candidate_results.append(lines)
                    calibration_scores[candidate_index] = _add_scores(
                        calibration_scores[candidate_index],
                        _score_ocr_result(lines),
                    )
                calibrated_frames += 1
                if calibrated_frames >= calibration_frame_count:
                    best_index = max(range(len(subtitle_crops)), key=lambda index: calibration_scores[index])
                    selected_subtitle_crop = subtitle_crops[best_index]
            else:
                prepared = _prepare_subtitle_crop(frame_image, selected_subtitle_crop)
                result, _ = engine(prepared)
                lines = _filter_ocr_lines(_extract_text_lines(result))
                candidate_results.append(lines)
                if _is_poor_crop_result(lines):
                    for crop in subtitle_crops:
                        if crop == selected_subtitle_crop:
                            continue
                        prepared = _prepare_subtitle_crop(frame_image, crop)
                        result, _ = engine(prepared)
                        candidate_results.append(_filter_ocr_lines(_extract_text_lines(result)))
        else:
            got_good_crop = False
            for candidate_index, crop in enumerate(crops, start=1):
                prepared = _prepare_subtitle_crop(frame_image, crop)
                result, _ = engine(prepared)
                lines = _filter_ocr_lines(_extract_text_lines(result))
                candidate_results.append(lines)
                if _is_good_crop_result(lines):
                    got_good_crop = True
                    break

        if not got_good_crop:
            full_frame_result, _ = engine(frame_image)
            candidate_results.append(_filter_ocr_lines(_extract_text_lines(full_frame_result)))

        best_lines = max(candidate_results, key=_score_ocr_result) if candidate_results else []
        if not best_lines:
            if frames_are_subtitle_crops:
                prev_signature = curr_signature
            else:
                prev_pixels = curr_pixels
            continue
        frame_groups.append(best_lines)
        if frames_are_subtitle_crops:
            prev_signature = curr_signature
        else:
            prev_pixels = curr_pixels
        prev_lines = best_lines
    return "\n".join(_fuse_frame_results(frame_groups)).strip()
